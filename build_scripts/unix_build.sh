#!/bin/bash

# Your base PyInstaller command
PYINSTALLER_CMD="pyinstaller -w --onefile -n "EdgeNodeLauncher" main.py"

# Combine the base command with the hidden imports and execute
echo "$PYINSTALLER_CMD"
eval "$PYINSTALLER_CMD"
