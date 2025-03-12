@echo off
setlocal EnableDelayedExpansion

set APP_NAME=EdgeNodeLauncher
set OUTPUT_DIR=dist

REM Check if EXE exists
if not exist "%OUTPUT_DIR%\%APP_NAME%.exe" (
    echo Error: %OUTPUT_DIR%\%APP_NAME%.exe not found.
    echo Please run build_exe.bat first to create the EXE.
    exit /b 1
)

echo Building MSI installer...

REM Check if WiX toolset is installed
where candle >nul 2>&1
if errorlevel 1 (
    echo Error: WiX Toolset not found. Please install WiX Toolset v3.11 or later.
    echo Download from: https://wixtoolset.org/releases/
    exit /b 1
)

REM Create temporary WiX files directory
if not exist wix mkdir wix

REM Create WiX source file
echo ^<?xml version="1.0" encoding="UTF-8"?^> > wix\product.wxs
echo ^<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi"^> >> wix\product.wxs
echo     ^<Product Id="*" Name="%APP_NAME%" Language="1033" Version="1.0.0.0" Manufacturer="Your Company" UpgradeCode="61DAB716-7CE9-4F67-BC46-7ADB96FB074A"^> >> wix\product.wxs
echo         ^<Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" /^> >> wix\product.wxs
echo         ^<MajorUpgrade DowngradeErrorMessage="A newer version of [ProductName] is already installed." /^> >> wix\product.wxs
echo         ^<MediaTemplate EmbedCab="yes" /^> >> wix\product.wxs
echo         ^<Feature Id="ProductFeature" Title="%APP_NAME%" Level="1"^> >> wix\product.wxs
echo             ^<ComponentGroupRef Id="ProductComponents" /^> >> wix\product.wxs
echo         ^</Feature^> >> wix\product.wxs
echo         ^<Icon Id="AppIcon.ico" SourceFile="assets\r1_icon.ico"/^> >> wix\product.wxs
echo         ^<Property Id="ARPPRODUCTICON" Value="AppIcon.ico" /^> >> wix\product.wxs
echo         ^<Property Id="ARPHELPLINK" Value="https://your-company-website.com" /^> >> wix\product.wxs
echo         ^<Property Id="ARPURLINFOABOUT" Value="https://your-company-website.com/about" /^> >> wix\product.wxs
echo         ^<UIRef Id="WixUI_Minimal" /^> >> wix\product.wxs
echo         ^<WixVariable Id="WixUIDialogBmp" Value="assets\r1_icon.png" /^> >> wix\product.wxs
echo         ^<WixVariable Id="WixUIBannerBmp" Value="assets\r1_icon.png" /^> >> wix\product.wxs
echo         ^<Directory Id="TARGETDIR" Name="SourceDir"^> >> wix\product.wxs
echo             ^<Directory Id="ProgramFilesFolder"^> >> wix\product.wxs
echo                 ^<Directory Id="INSTALLFOLDER" Name="%APP_NAME%"^> >> wix\product.wxs
echo                     ^<Component Id="ApplicationComponent" Guid="*"^> >> wix\product.wxs
echo                         ^<File Id="IconResource" Source="assets\r1_icon.ico" /^> >> wix\product.wxs
echo                         ^<File Id="ApplicationExecutable" Source="%OUTPUT_DIR%\%APP_NAME%.exe" KeyPath="yes"^> >> wix\product.wxs
echo                             ^<Shortcut Id="ApplicationStartMenuShortcut" Directory="ProgramMenuDir" Name="%APP_NAME%" WorkingDirectory="INSTALLFOLDER" Advertise="yes" Icon="AppIcon.ico" /^> >> wix\product.wxs
echo                             ^<Shortcut Id="ApplicationDesktopShortcut" Directory="DesktopFolder" Name="%APP_NAME%" WorkingDirectory="INSTALLFOLDER" Advertise="yes" Icon="AppIcon.ico" /^> >> wix\product.wxs
echo                         ^</File^> >> wix\product.wxs
echo                         ^<ProgId Id="%APP_NAME%.Document" Description="%APP_NAME% Application" Icon="AppIcon.ico"^> >> wix\product.wxs
echo                             ^<Extension Id="exe" ContentType="application/exe"^> >> wix\product.wxs
echo                                 ^<Verb Id="open" Command="Open" TargetFile="ApplicationExecutable" Argument="%%1" /^> >> wix\product.wxs
echo                             ^</Extension^> >> wix\product.wxs
echo                         ^</ProgId^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKLM" Key="SOFTWARE\Classes\Applications\%APP_NAME%.exe\DefaultIcon" Type="string" Value="[INSTALLFOLDER]%APP_NAME%.exe,0" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKLM" Key="SOFTWARE\Classes\Applications\%APP_NAME%.exe\shell\open\command" Type="string" Value="&quot;[INSTALLFOLDER]%APP_NAME%.exe&quot; &quot;%%1&quot;" /^> >> wix\product.wxs
    
REM Additional registry entries for thorough icon integration
echo                         ^<RegistryValue Root="HKLM" Key="SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\%APP_NAME%.exe" Type="string" Value="[INSTALLFOLDER]%APP_NAME%.exe" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKLM" Key="SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\%APP_NAME%.exe" Name="Path" Type="string" Value="[INSTALLFOLDER]" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKCU" Key="Software\Classes\%APP_NAME%File" Name="FriendlyTypeName" Type="string" Value="%APP_NAME% File" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKCU" Key="Software\Classes\%APP_NAME%File\DefaultIcon" Type="string" Value="[INSTALLFOLDER]%APP_NAME%.exe,0" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKLM" Key="SOFTWARE\Classes\%APP_NAME%.exe" Name="FriendlyAppName" Type="string" Value="%APP_NAME%" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKLM" Key="SOFTWARE\Classes\%APP_NAME%.exe\DefaultIcon" Type="string" Value="[INSTALLFOLDER]%APP_NAME%.exe,0" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKCU" Key="Software\Classes\Applications\%APP_NAME%.exe\DefaultIcon" Type="string" Value="[INSTALLFOLDER]%APP_NAME%.exe,0" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKCU" Key="Software\Classes\Applications\%APP_NAME%.exe\Taskbar\DefaultIcon" Type="string" Value="[INSTALLFOLDER]%APP_NAME%.exe,0" /^> >> wix\product.wxs
echo                     ^</Component^> >> wix\product.wxs
echo                 ^</Directory^> >> wix\product.wxs
echo             ^</Directory^> >> wix\product.wxs
echo             ^<Directory Id="ProgramMenuFolder"^> >> wix\product.wxs
echo                 ^<Directory Id="ProgramMenuDir" Name="%APP_NAME%"^> >> wix\product.wxs
echo                     ^<Component Id="ProgramMenuDir" Guid="*"^> >> wix\product.wxs
echo                         ^<RemoveFolder Id="ProgramMenuDir" On="uninstall" /^> >> wix\product.wxs
echo                         ^<RegistryValue Root="HKCU" Key="Software\[Manufacturer]\[ProductName]" Type="string" Value="" KeyPath="yes" /^> >> wix\product.wxs
echo                     ^</Component^> >> wix\product.wxs
echo                 ^</Directory^> >> wix\product.wxs
echo             ^</Directory^> >> wix\product.wxs
echo             ^<Directory Id="DesktopFolder" Name="Desktop" /^> >> wix\product.wxs
echo         ^</Directory^> >> wix\product.wxs
echo         ^<ComponentGroup Id="ProductComponents"^> >> wix\product.wxs
echo             ^<ComponentRef Id="ApplicationComponent" /^> >> wix\product.wxs
echo             ^<ComponentRef Id="ProgramMenuDir" /^> >> wix\product.wxs
echo         ^</ComponentGroup^> >> wix\product.wxs
echo     ^</Product^> >> wix\product.wxs
echo ^</Wix^> >> wix\product.wxs

REM Compile WiX source
echo Compiling WiX source...
candle wix\product.wxs -o wix\product.wixobj
if errorlevel 1 (
    echo Failed to compile WiX source.
    exit /b 1
)

REM Check for WiX UI Extension
echo Checking for WiX UI Extension...
where light >nul 2>&1
if not errorlevel 1 (
    set "LIGHT_ARGS=-ext WixUIExtension"
) else (
    set "LIGHT_ARGS="
    echo Warning: WixUIExtension not found. Installer will not have a custom UI.
)

echo Linking MSI installer...
light %LIGHT_ARGS% -out %OUTPUT_DIR%\%APP_NAME%.msi wix\product.wixobj
if errorlevel 1 (
    echo Failed to link MSI installer.
    exit /b 1
)

echo MSI installer built successfully: %OUTPUT_DIR%\%APP_NAME%.msi

endlocal 