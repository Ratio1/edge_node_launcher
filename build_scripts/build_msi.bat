@echo off
setlocal EnableDelayedExpansion

set APP_NAME=EdgeNodeLauncher
set OUTPUT_DIR=dist

REM Check if EXE exists
if not exist "%OUTPUT_DIR%\%APP_NAME%.exe" (
    echo Error: %OUTPUT_DIR%\%APP_NAME%.exe not found.
    echo Please run win32_build.bat first to create the EXE.
    exit /b 1
)

echo Building MSI installer...

REM Create temporary WiX files directory
if not exist wix mkdir wix

REM Create EULA directly in the wix directory
echo Generating EULA file...
(
echo {\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1033{\fonttbl{\f0\fnil\fcharset0 Calibri;}}
echo {\*\generator Riched20 10.0.19041}\viewkind4\uc1
echo \pard\sa200\sl276\slmult1\f0\fs22\lang9 END USER LICENSE AGREEMENT FOR EDGENODELAUNCHER\par
echo \par
echo IMPORTANT: PLEASE READ THIS END USER LICENSE AGREEMENT CAREFULLY BEFORE INSTALLING THE EDGENODELAUNCHER APPLICATION.\par
echo \par
echo By installing or using the EdgeNodeLauncher application, you agree to be bound by the terms of this Agreement. If you do not agree, do not install or use the application.\par
echo \par
echo 1. LICENSE GRANT\par
echo You are granted a non-exclusive license to use the software for personal or business purposes.\par
echo \par
echo 2. RESTRICTIONS\par
echo You may not reverse engineer, decompile, or disassemble the software.\par
echo \par
echo 3. NO WARRANTY\par
echo THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.\par
echo \par
echo 4. LIMITATION OF LIABILITY\par
echo IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DAMAGES ARISING FROM THE USE OF THIS SOFTWARE.\par
echo \par
echo 5. GOVERNING LAW\par
echo This agreement is governed by the laws of the jurisdiction where the software owner is located.\par
echo }
) > "wix\License.rtf"

REM Verify EULA file was created
if not exist "wix\License.rtf" (
    echo ERROR: Failed to create EULA file.
    exit /b 1
)

echo EULA file created successfully.
echo =============EULA CONTENT:=============
type "wix\License.rtf"
echo =======================================

REM Create a dead-simple WiX file with minimal features
echo ^<?xml version="1.0" encoding="UTF-8"?^> > wix\product.wxs
echo ^<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi"^> >> wix\product.wxs
echo   ^<Product Id="*" Name="EdgeNodeLauncher" Language="1033" Version="1.0.0.0" Manufacturer="YourCompany" UpgradeCode="61DAB716-7CE9-4F67-BC46-7ADB96FB074A"^> >> wix\product.wxs
echo     ^<Package InstallerVersion="200" Compressed="yes" /^> >> wix\product.wxs
echo     ^<MediaTemplate EmbedCab="yes" /^> >> wix\product.wxs
echo     ^<Icon Id="AppIcon.ico" SourceFile="%OUTPUT_DIR%\%APP_NAME%.exe" /^> >> wix\product.wxs
echo     ^<Property Id="ARPPRODUCTICON" Value="AppIcon.ico" /^> >> wix\product.wxs
echo     ^<WixVariable Id="WixUILicenseRtf" Value="wix\License.rtf" /^> >> wix\product.wxs
echo     ^<Feature Id="ProductFeature" Title="EdgeNodeLauncher" Level="1"^> >> wix\product.wxs
echo       ^<ComponentRef Id="ApplicationComponent" /^> >> wix\product.wxs
echo       ^<ComponentRef Id="DesktopShortcutComponent" /^> >> wix\product.wxs
echo     ^</Feature^> >> wix\product.wxs
echo     ^<Directory Id="TARGETDIR" Name="SourceDir"^> >> wix\product.wxs
echo       ^<Directory Id="ProgramFilesFolder"^> >> wix\product.wxs
echo         ^<Directory Id="INSTALLDIR" Name="EdgeNodeLauncher"^> >> wix\product.wxs
echo           ^<Component Id="ApplicationComponent" Guid="*"^> >> wix\product.wxs
echo             ^<File Id="ApplicationExe" Source="%OUTPUT_DIR%\%APP_NAME%.exe" KeyPath="yes" /^> >> wix\product.wxs
echo           ^</Component^> >> wix\product.wxs
echo         ^</Directory^> >> wix\product.wxs
echo       ^</Directory^> >> wix\product.wxs
echo       ^<Directory Id="DesktopFolder" Name="Desktop"^> >> wix\product.wxs
echo         ^<Component Id="DesktopShortcutComponent" Guid="*"^> >> wix\product.wxs
echo           ^<Shortcut Id="DesktopShortcut" >> wix\product.wxs
echo                     Name="EdgeNodeLauncher" >> wix\product.wxs
echo                     Description="Launch the Edge Node Launcher application" >> wix\product.wxs
echo                     Target="[INSTALLDIR]%APP_NAME%.exe" >> wix\product.wxs
echo                     WorkingDirectory="INSTALLDIR" >> wix\product.wxs
echo                     Icon="AppIcon.ico" /^> >> wix\product.wxs
echo           ^<RemoveFolder Id="DesktopFolder" On="uninstall" /^> >> wix\product.wxs
echo           ^<RegistryValue Root="HKCU" Key="Software\EdgeNodeLauncher" Name="installed" Type="integer" Value="1" KeyPath="yes" /^> >> wix\product.wxs
echo         ^</Component^> >> wix\product.wxs
echo       ^</Directory^> >> wix\product.wxs
echo     ^</Directory^> >> wix\product.wxs
echo     ^<Property Id="WIXUI_INSTALLDIR" Value="INSTALLDIR" /^> >> wix\product.wxs
echo     ^<UIRef Id="WixUI_InstallDir" /^> >> wix\product.wxs
echo   ^</Product^> >> wix\product.wxs
echo ^</Wix^> >> wix\product.wxs

REM Show the contents of the WiX directory to verify EULA is there
echo Files in WiX directory:
dir wix

REM Compile WiX source
echo Compiling WiX source...
candle wix\product.wxs -o wix\product.wixobj
if errorlevel 1 (
    echo Failed to compile WiX source.
    exit /b 1
)

REM Link MSI installer
echo Linking MSI installer...
light -ext WixUIExtension -out %OUTPUT_DIR%\%APP_NAME%.msi wix\product.wixobj
if errorlevel 1 (
    echo Failed to link MSI installer.
    exit /b 1
)

echo MSI installer built successfully: %OUTPUT_DIR%\%APP_NAME%.msi

endlocal 