"""Nuke menu integration for NukeMCP.

Place this file (and nuke_mcp_addon.py) in your .nuke directory or NUKE_PATH.
"""

import nuke

toolbar = nuke.menu("Nodes")
nuke_mcp_menu = toolbar.addMenu("NukeMCP")
nuke_mcp_menu.addCommand(
    "Start Server",
    "import nuke_mcp_addon; nuke_mcp_addon.start()",
)
