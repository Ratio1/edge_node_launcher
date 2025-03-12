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
echo EXE package built successfully.

REM Sign the EXE
echo Signing the EXE...
set CERT_NAME=
set TIMESTAMP_SERVER=http://timestamp.digicert.com

REM Check for certificate details
if "%CERT_NAME%"=="" (
    echo No certificate name specified. Please set CERT_NAME environment variable or edit this script.
    set /p CERT_NAME="Enter certificate name from store (leave empty to skip signing): "
)

if not "%CERT_NAME%"=="" (
    echo Signing with certificate: %CERT_NAME%
    
    REM Check if signtool is available in PATH
    where signtool >nul 2>&1
    if errorlevel 1 (
        echo Warning: signtool.exe not found in PATH. Attempting to locate it...
        
        REM Try to find signtool in Windows SDK
        for /f %%i in ('dir /b /s "C:\Program Files*\Windows Kits\*\bin\*\x64\signtool.exe" 2^>nul') do set SIGNTOOL=%%i
        
        if not defined SIGNTOOL (
            echo Error: signtool.exe not found. Please install Windows SDK or add signtool to PATH.
            echo Skipping signing process.
            goto :skip_signing
        )
    ) else (
        set SIGNTOOL=signtool
    )
    
    echo Using signtool: %SIGNTOOL%
    
    %SIGNTOOL% sign /n "%CERT_NAME%" /fd SHA256 /tr "%TIMESTAMP_SERVER%" /td SHA256 /v "%OUTPUT_DIR%\%APP_NAME%.exe"
    if errorlevel 1 (
        echo Warning: Failed to sign the EXE.
    ) else (
        echo EXE signed successfully.
    )
)

:skip_signing

echo.
echo Build summary:
echo - EXE package: %OUTPUT_DIR%\%APP_NAME%.exe
echo.

REM Run post-build tasks
echo Running post-build tasks...
call "%~dp0\post_build.bat"
echo.

endlocal