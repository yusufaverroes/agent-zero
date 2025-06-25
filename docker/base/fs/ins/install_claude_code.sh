#!/bin/bash
set -e

echo "====================CLAUDE CODE CLI START===================="

# Install Claude Code CLI globally
npm install -g @anthropic-ai/claude-code

# Verify installation
if command -v claude &> /dev/null; then
    echo "Claude Code CLI installed successfully"
    claude --version || echo "Claude Code CLI installed but version check failed (normal for first run)"
else
    echo "ERROR: Claude Code CLI installation failed"
    exit 1
fi

# Create directory for Claude credentials persistence
mkdir -p /root/.claude
chmod 700 /root/.claude

echo "====================CLAUDE CODE CLI END===================="