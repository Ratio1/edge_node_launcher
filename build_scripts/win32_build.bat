@echo off
setlocal EnableDelayedExpansion

REM Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "EdgeNodeLauncher.spec" del "EdgeNodeLauncher.spec"

REM Set environment variables to optimize Python and suppress debug output
set PYTHONOPTIMIZE=1
set PYTHONHOME=
set PYTHONDONTWRITEBYTECODE=1
set PYTHONUNBUFFERED=1

REM Your base PyInstaller command with additional options for console suppression
set PYINSTALLER_CMD=pyinstaller --noconsole --windowed --onefile --clean --noconfirm ^
  --manifest=app.manifest ^
  --name="EdgeNodeLauncher" ^
  --icon=assets\r1_icon.ico ^
  --add-data "assets\r1_icon.ico;assets" ^
  --log-level=WARN ^
  launcher.py
set APP_NAME=EdgeNodeLauncher
set OUTPUT_DIR=dist

echo Building EXE package...
echo %PYINSTALLER_CMD%
%PYINSTALLER_CMD%
if errorlevel 1 (
    echo Failed to build EXE package.
    exit /b 1
)
echo EXE package built successfully: %OUTPUT_DIR%\%APP_NAME%.exe

REM Run post-build tasks
echo Running post-build tasks...
call "%~dp0\post_build.bat"
echo.

endlocal