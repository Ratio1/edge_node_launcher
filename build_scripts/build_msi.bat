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

REM Copy EULA.rtf to the wix directory
copy build_scripts\EULA.rtf wix\EULA.rtf

REM Create a dead-simple WiX file with minimal features
echo ^<?xml version="1.0" encoding="UTF-8"?^> > wix\product.wxs
echo ^<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi"^> >> wix\product.wxs
echo   ^<Product Id="*" Name="EdgeNodeLauncher" Language="1033" Version="1.0.0.0" Manufacturer="YourCompany" UpgradeCode="61DAB716-7CE9-4F67-BC46-7ADB96FB074A"^> >> wix\product.wxs
echo     ^<Package InstallerVersion="200" Compressed="yes" /^> >> wix\product.wxs
echo     ^<MediaTemplate EmbedCab="yes" /^> >> wix\product.wxs
echo     ^<Icon Id="AppIcon.ico" SourceFile="%OUTPUT_DIR%\%APP_NAME%.exe" /^> >> wix\product.wxs
echo     ^<Property Id="ARPPRODUCTICON" Value="AppIcon.ico" /^> >> wix\product.wxs
echo     ^<WixVariable Id="WixUILicenseRtf" Value="wix\EULA.rtf" /^> >> wix\product.wxs
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