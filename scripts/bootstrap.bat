@echo off
setlocal

set REPO=https://github.com/kleer001/nuke-mcp.git
set DIR=nuke-mcp

echo === NukeMCP Bootstrap ===
echo.

if not exist pyproject.toml (
    echo Cloning nuke-mcp...
    git clone %REPO% %DIR%
    cd %DIR%
    echo.
)

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing uv...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
)

echo Installing dependencies...
uv sync
echo.

echo === Done ===
echo.
echo Next steps:
echo   1. Copy the Nuke addon:
echo        copy nuke_addon\nuke_mcp_addon.py %%USERPROFILE%%\.nuke\
echo.
echo   2. In Nuke's Script Editor:
echo        import nuke_mcp_addon; nuke_mcp_addon.start()
echo.
echo   3. Test without Nuke:
echo        uv run nuke-mcp --mock
echo.
echo See README for MCP client configuration.
