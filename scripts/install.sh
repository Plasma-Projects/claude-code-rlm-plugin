#!/bin/bash

# Claude Code RLM Plugin Installation Script

set -e

PLUGIN_NAME="recursive-language-model"
PLUGIN_DIR="$HOME/.config/opencode/plugins/rlm"
SKILLS_DIR="$HOME/.claude/skills"

echo "Installing Claude Code RLM Plugin..."

# Create directories
mkdir -p "$PLUGIN_DIR"
mkdir -p "$SKILLS_DIR"

# Copy plugin files
cp -r ./* "$PLUGIN_DIR/"

# Link skill
ln -sf "$PLUGIN_DIR/skills/rlm-auto-trigger" "$SKILLS_DIR/rlm-auto-trigger"

# Set permissions
chmod +x "$PLUGIN_DIR/scripts/install.sh"

echo "✓ RLM Plugin installed successfully"
echo ""
echo "Configuration: $PLUGIN_DIR/.claude-plugin/plugin.json"
echo "Auto-trigger skill: $SKILLS_DIR/rlm-auto-trigger"
echo ""
echo "The plugin will automatically activate for:"
echo "  • Files larger than 50KB"
echo "  • Contexts exceeding 100K tokens"
echo "  • Processing more than 10 files"
echo ""
echo "To test: /plugin test recursive-language-model"