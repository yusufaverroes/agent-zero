import subprocess
import json
import os
import asyncio
from typing import Dict, Optional, Tuple
from python.helpers.print_style import PrintStyle


class ClaudeAuthManager:
    """
    Manages Claude Code CLI authentication for Pro/Max plan users.
    Handles login, logout, and authentication status checking.
    """
    
    def __init__(self):
        self.claude_dir = os.path.expanduser("~/.claude")
        self.config_file = os.path.join(self.claude_dir, "config.json")
        
    def is_claude_cli_installed(self) -> bool:
        """Check if Claude Code CLI is installed and available."""
        try:
            result = subprocess.run(
                ["which", "claude"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_auth_status(self) -> Tuple[bool, Optional[str]]:
        """
        Check if user is authenticated with Claude Pro/Max.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_authenticated, error_message)
        """
        if not self.is_claude_cli_installed():
            return False, "Claude Code CLI is not installed"
            
        try:
            # Try to run a simple command that requires authentication
            result = subprocess.run(
                ["claude", "--help"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            # If help command works, CLI is installed
            # Check for authentication by looking for config files
            if os.path.exists(self.claude_dir):
                config_files = os.listdir(self.claude_dir)
                if any(f.endswith('.json') for f in config_files):
                    return True, None
                    
            return False, "Not authenticated with Claude Pro/Max account"
            
        except subprocess.TimeoutExpired:
            return False, "Claude CLI timeout - possible authentication issue"
        except FileNotFoundError:
            return False, "Claude Code CLI not found"
        except Exception as e:
            return False, f"Error checking authentication: {str(e)}"
    
    async def initiate_login(self) -> Tuple[bool, str]:
        """
        Initiate Claude Pro/Max login process.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self.is_claude_cli_installed():
            return False, "Claude Code CLI is not installed"
            
        try:
            # Create claude directory if it doesn't exist
            os.makedirs(self.claude_dir, exist_ok=True)
            
            PrintStyle(font_color="blue", padding=True).print(
                "Initiating Claude Pro/Max login process..."
            )
            
            # Run claude command to trigger initial setup
            # This will prompt for authentication
            process = subprocess.Popen(
                ["claude"], 
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send exit command to close after initialization
            stdout, stderr = process.communicate(input="/exit\n", timeout=30)
            
            # Check if authentication was successful
            is_auth, error = self.check_auth_status()
            
            if is_auth:
                return True, "Successfully authenticated with Claude Pro/Max"
            else:
                return False, f"Authentication failed: {error}"
                
        except subprocess.TimeoutExpired:
            return False, "Login process timed out. Please try again."
        except Exception as e:
            return False, f"Login failed: {str(e)}"
    
    def logout(self) -> Tuple[bool, str]:
        """
        Logout and clear Claude authentication.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Remove claude configuration directory
            if os.path.exists(self.claude_dir):
                import shutil
                shutil.rmtree(self.claude_dir)
                
            return True, "Successfully logged out from Claude"
            
        except Exception as e:
            return False, f"Logout failed: {str(e)}"
    
    def get_auth_info(self) -> Dict[str, any]:
        """
        Get detailed authentication information.
        
        Returns:
            Dict containing authentication status and details
        """
        is_installed = self.is_claude_cli_installed()
        is_auth, error = self.check_auth_status()
        
        return {
            "cli_installed": is_installed,
            "authenticated": is_auth,
            "error": error,
            "config_dir": self.claude_dir,
            "config_exists": os.path.exists(self.claude_dir)
        }
    
    async def test_claude_connection(self) -> Tuple[bool, str]:
        """
        Test Claude connection with a simple query.
        
        Returns:
            Tuple[bool, str]: (success, response_or_error)
        """
        is_auth, error = self.check_auth_status()
        if not is_auth:
            return False, f"Not authenticated: {error}"
            
        try:
            # Try a simple test query
            result = subprocess.run(
                ["claude", "-p", "Hello, can you respond with just 'OK'?"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Connection test successful"
            else:
                return False, f"Connection test failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Connection test timed out"
        except Exception as e:
            return False, f"Connection test error: {str(e)}"


# Global instance
claude_auth_manager = ClaudeAuthManager()