import os
import sys
import requests
import zipfile
import shutil
import platform
import subprocess
from PyQt5.QtWidgets import QMessageBox

from ver import __VER__ as CURRENT_VERSION

GITHUB_API_URL = 'https://api.github.com/repos/vitalii-t12/edge_node_launcher_private/releases/latest'
# GITHUB_API_URL = 'https://api.github.com/repos/Ratio1/edge_node_launcher/releases/latest'
DOWNLOAD_DIR = 'downloads'

class _UpdaterMixin:

  @staticmethod
  def get_latest_release_version():
    response = requests.get(GITHUB_API_URL)
    response.raise_for_status()
    latest_release = response.json()
    latest_version = latest_release['tag_name']
    assets = latest_release['assets']
    download_urls = {
      'Windows': next(asset['browser_download_url'] for asset in assets if 'Windows' in asset['name'] and '.exe' in asset['name']),
      'Linux_Ubuntu_24.04': next(asset['browser_download_url'] for asset in assets if 'Ubuntu-24.04' in asset['name']),
      'Linux_Ubuntu_22.04': next(asset['browser_download_url'] for asset in assets if 'Ubuntu-22.04' in asset['name']),
      'Linux_Ubuntu_20.04': next(asset['browser_download_url'] for asset in assets if 'Ubuntu-20.04' in asset['name']),
      'Darwin': next(asset['browser_download_url'] for asset in assets if 'macOS' in asset['name'] and '.zip' in asset['name']),
    }
    return latest_version, download_urls

  def _compare_versions(self, current_version, latest_version):
    latest_version = latest_version.lstrip('v').strip().replace('"', '').replace("'", '')
    result = False
    self.add_log(f'Comparing versions: {current_version} -> {latest_version}')
    current_version_parts = [int(part) for part in current_version.split('.')]
    latest_version_parts = [int(part) for part in latest_version.split('.')]
    if latest_version_parts > current_version_parts:
      result = True
    else:
      if latest_version_parts < current_version_parts:
        self.add_log('Your version is newer than the latest version. Are you a time traveler or a dev?')
    return result

  def _download_update(self, download_url, download_dir):
    os.makedirs(download_dir, exist_ok=True)
    
    # Get the appropriate file extension based on platform and URL
    if sys.platform == "win32":
      local_filename = os.path.join(download_dir, 'EdgeNodeLauncher.exe')
    elif sys.platform == "darwin":
      local_filename = os.path.join(download_dir, 'update.zip')
    else:  # Linux
      local_filename = os.path.join(download_dir, 'EdgeNodeLauncher.AppImage')
    
    self.add_log(f'Downloading to {local_filename}')
    with requests.get(download_url, stream=True) as response:
      response.raise_for_status()
      with open(local_filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
          file.write(chunk)
    return local_filename

  def _extract_zip(self, zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
      zip_ref.extractall(extract_to)


  def _replace_executable(self, download_path, executable_name):
    current_executable = sys.executable
    if current_executable.endswith('python.exe') or current_executable.endswith('python'):
      raise Exception('Cannot replace the current executable as it is running in a virtual environment.')
    
    self.add_log(f'Preparing executable replacement of: {current_executable}')
    
    if sys.platform == "win32":
      # For Windows, we download the .exe directly
      new_executable = download_path
      current_folder = os.path.dirname(current_executable)
      executable_basename = os.path.basename(current_executable)
      
      # Check if the target directory needs admin privileges
      requires_admin = any(folder in current_folder.lower() for folder in ['program files', 'program files (x86)', 'windows', 'system32'])
      
      # Create a batch script to replace the executable after the current process exits
      script_path = os.path.join(os.path.dirname(download_path), 'replace_executable.bat')
      
      self.add_log(f"Executable to replace: {executable_basename}", debug=True)
      
      # Use xcopy instead of copy for better error handling
      move_cmd = f'xcopy /Y /F "{new_executable}" "{current_executable}"'
      
      self.add_log(f"Copy command: {move_cmd}", debug=True)
      self.add_log(f"Creating update script: {script_path}", debug=True)
      
      # Get process IDs for current app before closing
      try:
          import psutil
          current_pid = os.getpid()
          self.add_log(f"Current process ID: {current_pid}", debug=True)
      except ImportError:
          current_pid = None
          self.add_log("psutil not available to get process ID", debug=True)
      
      # Create the batch file with proper admin elevation
      with open(script_path, 'w') as script:
        # Add UAC elevation script for admin privileges
        if requires_admin:
          script.write(f"""@echo off
echo ========================================
echo EdgeNodeLauncher Update Process
echo ========================================
echo Starting update process...

:: Check for Admin rights and if not present, elevate
>nul 2>&1 "%SYSTEMROOT%\\system32\\cacls.exe" "%SYSTEMROOT%\\system32\\config\\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\\getadmin.vbs"
    "%temp%\\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\\getadmin.vbs" ( del "%temp%\\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

echo Administrative privileges acquired.
echo Waiting for application to close...

:: Wait for the application to close with a timeout
set MAX_WAIT=30
set COUNTER=0

:loop
tasklist /FI "IMAGENAME eq {executable_basename}" 2>NUL | find /I "{executable_basename}" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Process {executable_basename} is still running... (%COUNTER%/%MAX_WAIT% seconds)
    set /a COUNTER+=1
    if %COUNTER% GEQ %MAX_WAIT% (
        echo Process wait timeout reached. Attempting to force proceed.
        choice /C YN /M "Process did not exit. Try to update anyway?"
        if errorlevel 2 goto :cancel
        goto :proceed
    )
    timeout /T 1 /NOBREAK >NUL
    goto loop
)

:proceed
echo No running instances of {executable_basename} found or timeout reached.
echo Application closed. Copying new version...

:: Copy the new executable
{move_cmd}
if %errorlevel% neq 0 (
    echo Failed to copy file. Error code: %errorlevel%
    echo This might be because the file is still in use.
    echo.
    pause
    exit /B %errorlevel%
)

echo Update successful. Launching application...
timeout /T 2 /NOBREAK >NUL
start "" "{current_executable}"
echo Done.
del "%~f0"
exit

:cancel
echo Update cancelled by user.
pause
exit /B 1
""")
        else:
          # Regular non-admin script for user directories
          script.write(f"""@echo off
echo ========================================
echo EdgeNodeLauncher Update Process
echo ========================================
echo Starting update process...
echo Waiting for application to close...

:: Wait for the application to close with a timeout
set MAX_WAIT=30
set COUNTER=0

:loop
tasklist /FI "IMAGENAME eq {executable_basename}" 2>NUL | find /I "{executable_basename}" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Process {executable_basename} is still running... (%COUNTER%/%MAX_WAIT% seconds)
    set /a COUNTER+=1
    if %COUNTER% GEQ %MAX_WAIT% (
        echo Process wait timeout reached. Attempting to force proceed.
        choice /C YN /M "Process did not exit. Try to update anyway?"
        if errorlevel 2 goto :cancel
        goto :proceed
    )
    timeout /T 1 /NOBREAK >NUL
    goto loop
)

:proceed
echo No running instances of {executable_basename} found or timeout reached.
echo Application closed. Copying new version...

:: Copy the new executable
{move_cmd}
if %errorlevel% neq 0 (
    echo Failed to copy file. Error code: %errorlevel%
    echo This might be because the file is still in use.
    echo.
    pause
    exit /B %errorlevel%
)

echo Update successful. Launching application...
timeout /T 2 /NOBREAK >NUL
start "" "{current_executable}"
echo Done.
del "%~f0"
exit

:cancel
echo Update cancelled by user.
pause
exit /B 1
""")

      # Execute the batch script in a new window so user can see the progress
      self.add_log(f'Batch script created: {script_path}')
      
      # Run with a visible window directly without a launcher script
      self.add_log(f'Executing updater script: {script_path}')
      
      # Try to kill any existing updater processes first
      try:
          for proc in subprocess.check_output(["tasklist", "/FI", "WINDOWTITLE eq EdgeNodeLauncher Update"]).decode().strip().split('\n'):
              if "cmd.exe" in proc:
                  pid = int(proc.split()[1])
                  subprocess.call(["taskkill", "/F", "/PID", str(pid)])
      except Exception as e:
          self.add_log(f"Failed to kill existing updater processes: {e}", debug=True)
      
      # Start the update script with a visible window
      subprocess.Popen(["cmd", "/c", "start", "EdgeNodeLauncher Update", script_path], shell=True)

    elif sys.platform == "darwin":
      # For macOS, we need to handle the app bundle
      extract_dir = os.path.dirname(download_path)
      app_bundle = None
      
      # Find the .app bundle in the extracted directory
      for item in os.listdir(extract_dir):
          if item.endswith('.app'):
              app_bundle = os.path.join(extract_dir, item)
              break
      
      if not app_bundle:
          raise Exception("Could not find .app bundle in extracted files")
      
      # Get the current app bundle path
      current_app_path = os.path.abspath(os.path.join(current_executable, '..', '..'))
      temp_script_path = os.path.join(extract_dir, 'replace_app.sh')
      
      with open(temp_script_path, 'w') as script:
          script.write(f"""#!/bin/bash
          while pgrep -f "{os.path.basename(current_executable)}" > /dev/null; do sleep 1; done
          rm -rf "{current_app_path}"
          cp -R "{app_bundle}" "{os.path.dirname(current_app_path)}"
          open "{current_app_path}"
          rm -- "$0"
          """)
      
      os.chmod(temp_script_path, 0o755)
      subprocess.Popen(['sh', temp_script_path])
      self.add_log(f'Shell script created and executed: {temp_script_path}')

    else:
      # For Linux, download the AppImage directly
      new_executable = download_path
      temp_executable = os.path.join(os.path.dirname(download_path), executable_name + '_new.AppImage')

      # Copy the new executable to a temporary location
      shutil.copy(new_executable, temp_executable)
      self.add_log(f'New AppImage copied to temporary location: {temp_executable}')

      # Create a shell script to replace the executable after the current process exits
      script_path = os.path.join(os.path.dirname(download_path), 'replace_executable.sh')
      with open(script_path, 'w') as script:
        script.write(f"""
        #!/bin/bash
        while pgrep -f "{os.path.basename(current_executable)}" > /dev/null; do sleep 1; done
        mv "{temp_executable}" "{current_executable}"
        chmod +x "{current_executable}"
        "{current_executable}" &
        rm -- "$0"
        """)

      # Make the shell script executable and run it
      os.chmod(script_path, 0o755)
      subprocess.Popen(['sh', script_path])
      self.add_log(f'Shell script created and executed: {script_path}')

    # Exit the current application
    QMessageBox.information(None, 'Update Complete', 'The application will now restart to complete the update.')    
    sys.exit()
    return


  def check_for_updates(self, verbose=True):
    try:
      latest_version, download_urls = self.get_latest_release_version()
      latest_version = latest_version.lstrip('v').strip().replace('"', '').replace("'", '')
      if verbose:
        self.add_log(f'Obtained latest version: {latest_version}')
      if self._compare_versions(CURRENT_VERSION, latest_version):
        reply = QMessageBox.question(None, 'Update Available',
                                    f'A new version v{latest_version} is available (current v{CURRENT_VERSION}). Do you want to update?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
          platform_system = platform.system()
          try:
            if platform_system == 'Windows':
              download_url = download_urls['Windows']
            elif platform_system == 'Linux':
              if '24.04' in platform.version():
                download_url = download_urls['Linux_Ubuntu_24.04']
              elif '22.04' in platform.version():
                download_url = download_urls['Linux_Ubuntu_22.04']
              elif '20.04' in platform.version():
                download_url = download_urls['Linux_Ubuntu_20.04']
              else:
                QMessageBox.information(None, 'Update Not Available', f'No update available for your Linux version: {platform.version()}.')
                return
            elif platform_system == 'Darwin':  # macOS
              download_url = download_urls['Darwin']
            else:
              QMessageBox.information(None, 'Update Not Available', f'No update available for your OS: {platform_system}.')
              return
          except (KeyError, StopIteration) as e:
            self.add_log(f"Failed to find download URL for your platform: {e}")
            QMessageBox.warning(None, 'Update Error', f'Could not find a compatible download for your system: {platform_system}.')
            return
              
          # Use user's temp directory for downloads to avoid permission issues
          if sys.platform == "win32":
            download_dir = os.path.join(os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA'), 'EdgeNodeLauncher', 'updates')
          else:
            download_dir = os.path.join(os.getcwd(), DOWNLOAD_DIR)
            
          os.makedirs(download_dir, exist_ok=True)
          self.add_log(f'Downloading update from {download_url} to {download_dir}...')
          
          # Download the update
          try:
            downloaded_file = self._download_update(download_url, download_dir)
            
            # For macOS, extract the zip file
            if platform_system == 'Darwin':
                self.add_log(f'Extracting update from {downloaded_file}...')
                self._extract_zip(downloaded_file, download_dir)
            
            # Show final confirmation before proceeding with update
            QMessageBox.information(None, 'Ready to Update', 
                                   'The update has been downloaded. The application will now close and update itself.\n\n' +
                                   'Please wait for the update process to complete.\n' +
                                   'If the application does not restart automatically after 1 minute, please start it manually.')
            
            # Replace the executable
            self._replace_executable(downloaded_file, 'EdgeNodeLauncher')
          except Exception as e:
            self.add_log(f"Error during download or installation: {str(e)}")
            QMessageBox.critical(None, 'Update Failed', f'Failed to download or install the update: {str(e)}')
      else:
        if verbose:
          self.add_log("You are already using the latest version. Current: {}, Online: {}".format(CURRENT_VERSION, latest_version))
    except Exception as e:
      self.add_log(f"Failed to check for updates: {e}")
      QMessageBox.warning(None, 'Update Check Failed', f'Could not check for updates: {str(e)}')

