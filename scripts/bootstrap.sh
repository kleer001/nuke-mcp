#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/kleer001/nuke-mcp.git"
DIR="nuke-mcp"

echo "=== NukeMCP Bootstrap ==="
echo ""

# Clone if we're not already inside the repo
if [ ! -f "pyproject.toml" ]; then
    echo "Cloning nuke-mcp..."
    git clone "$REPO" "$DIR"
    cd "$DIR"
    echo ""
fi

# Install uv if missing
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo ""
fi

echo "Installing dependencies..."
uv sync
echo ""

echo "=== Done ==="
echo ""
echo "Next steps:"
echo "  1. Copy the Nuke addon:"
echo "       cp nuke_addon/nuke_mcp_addon.py ~/.nuke/"
echo ""
echo "  2. In Nuke's Script Editor:"
echo "       import nuke_mcp_addon; nuke_mcp_addon.start()"
echo ""
echo "  3. Test without Nuke:"
echo "       uv run nuke-mcp --mock"
echo ""
echo "See README for MCP client configuration."
