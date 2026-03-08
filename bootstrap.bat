@echo off
echo === NukeMCP Bootstrap ===
echo.

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing uv...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
)

echo Installing dependencies...
uv sync
echo.

echo === Setup Complete ===
echo.
echo To run the MCP server (with mock Nuke for testing):
echo   uv run nuke-mcp --mock
echo.
echo To run with a live Nuke session:
echo   uv run nuke-mcp
echo.
echo To run tests:
echo   uv run pytest
echo.
echo === Nuke Addon Setup ===
echo.
echo Copy the addon files into your Nuke scripts directory:
echo   copy nuke_addon\nuke_mcp_addon.py %%USERPROFILE%%\.nuke\
echo   copy nuke_addon\menu.py %%USERPROFILE%%\.nuke\
echo.
