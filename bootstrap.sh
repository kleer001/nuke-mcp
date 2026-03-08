#!/usr/bin/env bash
set -euo pipefail

echo "=== NukeMCP Bootstrap ==="
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo ""
fi

echo "Installing dependencies..."
uv sync
echo ""

echo "=== Setup Complete ==="
echo ""
echo "To run the MCP server (with mock Nuke for testing):"
echo "  uv run nuke-mcp --mock"
echo ""
echo "To run with a live Nuke session:"
echo "  uv run nuke-mcp"
echo ""
echo "To run tests:"
echo "  uv run pytest"
echo ""
echo "=== Nuke Addon Setup ==="
echo ""
echo "Copy the addon files into your Nuke scripts directory:"
echo "  cp nuke_addon/nuke_mcp_addon.py ~/.nuke/"
echo "  cp nuke_addon/menu.py ~/.nuke/"
echo ""
echo "Or add this repo's nuke_addon/ directory to your NUKE_PATH."
echo ""
echo "=== Claude Code / Claude Desktop ==="
echo ""
echo "Add this to your .mcp.json or Claude Desktop config:"
echo ""
cat .mcp.json
echo ""
