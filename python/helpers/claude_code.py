import subprocess
import json
import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from langchain_core.callbacks.manager import AsyncCallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils import get_from_dict_or_env
from pydantic import Field

from python.helpers.claude_auth import claude_auth_manager
from python.helpers.print_style import PrintStyle


class ClaudeCodeChatModel(BaseChatModel):
    """
    Claude Code SDK integration for Agent Zero.
    Uses subprocess calls to Claude CLI for Pro/Max plan users.
    """
    
    model_name: str = Field(default="claude-3-5-sonnet-20241022")
    max_tokens: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    
    @property
    def _llm_type(self) -> str:
        return "claude-code"
    
    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """
        Convert LangChain messages to a prompt suitable for Claude CLI.
        """
        formatted_parts = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                formatted_parts.append(f"System: {message.content}")
            elif isinstance(message, HumanMessage):
                formatted_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                formatted_parts.append(f"Assistant: {message.content}")
            else:
                # Generic message handling
                formatted_parts.append(f"Message: {message.content}")
        
        # Combine all parts into a single prompt
        return "\n\n".join(formatted_parts)
    
    def _build_claude_command(self, prompt: str) -> List[str]:
        """
        Build the Claude CLI command with proper parameters.
        """
        cmd = ["claude", "-p", prompt]
        
        # Add model specification if needed
        if self.model_name and self.model_name != "claude-3-5-sonnet-20241022":
            cmd.extend(["--model", self.model_name])
        
        # Add output format for consistent parsing
        cmd.extend(["--output-format", "json"])
        
        return cmd
    
    async def _check_authentication(self) -> None:
        """
        Check if user is authenticated with Claude Pro/Max.
        """
        is_auth, error = claude_auth_manager.check_auth_status()
        if not is_auth:
            raise ValueError(f"Claude Code authentication required: {error}")
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Synchronous generation method (required by LangChain interface).
        """
        # Convert to async call
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self._agenerate(messages, stop, run_manager, **kwargs)
        )
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Asynchronous generation method.
        """
        await self._check_authentication()
        
        # Format messages for Claude CLI
        prompt = self._format_messages(messages)
        
        # Build command
        cmd = self._build_claude_command(prompt)
        
        try:
            # Execute Claude CLI command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=120  # 2 minute timeout
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Claude CLI failed: {error_msg}")
            
            # Parse response
            response_text = stdout.decode().strip()
            
            try:
                # Try to parse as JSON first
                response_data = json.loads(response_text)
                content = response_data.get('result', response_text)
            except json.JSONDecodeError:
                # Fallback to raw text
                content = response_text
            
            # Create chat generation
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except asyncio.TimeoutError:
            raise RuntimeError("Claude CLI request timed out")
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Claude Code error: {str(e)}"
            )
            raise RuntimeError(f"Claude Code execution failed: {str(e)}")
    
    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGeneration]:
        """
        Asynchronous streaming method.
        Note: Claude CLI doesn't support true streaming, so we simulate it.
        """
        await self._check_authentication()
        
        # Format messages for Claude CLI
        prompt = self._format_messages(messages)
        
        # Build command (remove JSON format for streaming to get raw output)
        cmd = ["claude", "-p", prompt]
        if self.model_name and self.model_name != "claude-3-5-sonnet-20241022":
            cmd.extend(["--model", self.model_name])
        
        try:
            # Execute Claude CLI command with streaming
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            
            # Read output in chunks to simulate streaming
            response_chunks = []
            
            while True:
                chunk = await process.stdout.read(1024)
                if not chunk:
                    break
                
                chunk_text = chunk.decode()
                response_chunks.append(chunk_text)
                
                # Yield chunk as ChatGeneration
                message = AIMessage(content=chunk_text)
                generation = ChatGeneration(message=message)
                
                # Callback for streaming
                if run_manager:
                    await run_manager.on_llm_new_token(chunk_text)
                
                yield generation
                
                # Small delay to simulate real streaming
                await asyncio.sleep(0.01)
            
            # Wait for process to complete
            stderr = await process.stderr.read()
            await process.wait()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"Claude CLI failed: {error_msg}")
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Claude Code streaming error: {str(e)}"
            )
            raise RuntimeError(f"Claude Code streaming failed: {str(e)}")
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return a dictionary of identifying parameters."""
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
    
    def get_num_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Claude CLI doesn't provide token counting, so we use a rough estimate.
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    async def test_connection(self) -> bool:
        """
        Test if Claude Code is working properly.
        """
        try:
            await self._check_authentication()
            
            # Simple test message
            test_messages = [HumanMessage(content="Hello, respond with just 'OK'")]
            result = await self._agenerate(test_messages)
            
            return len(result.generations) > 0
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Claude Code connection test failed: {str(e)}"
            )
            return False