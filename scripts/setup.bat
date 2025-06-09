@echo off
echo Installing WordPress MCP Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.
echo Next steps:
echo 1. Edit config/wordpress_sites.yaml with your WordPress sites
echo 2. Configure Claude Desktop with claude_desktop_config.json
echo 3. Run: python -m src.server
echo.
echo See README.md for detailed instructions
pause 