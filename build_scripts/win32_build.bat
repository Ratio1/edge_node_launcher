@echo off
setlocal EnableDelayedExpansion

REM Your base PyInstaller command
set PYINSTALLER_CMD=pyinstaller -w --onefile -n "EdgeNodeLauncher" --icon=assets\r1_icon.ico main.py

REM Combine the base command with the hidden imports and execute
echo %PYINSTALLER_CMD%
%PYINSTALLER_CMD%

endlocal