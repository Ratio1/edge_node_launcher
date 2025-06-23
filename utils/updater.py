import os
import sys
import requests
import zipfile
import shutil
import platform
import subprocess
from PyQt5.QtWidgets import QMessageBox, QApplication

from utils.const import GITHUB_API_URL
from ver import __VER__ as CURRENT_VERSION

DOWNLOAD_DIR = 'downloads'

class _UpdaterMixin:

  @staticmethod
  def get_latest_release_version():
    response = requests.get(GITHUB_API_URL)
    response.raise_for_status()
    latest_release = response.json()
    latest_version = latest_release['tag_name']
    assets = latest_release['assets']
    
    # Helper function to safely find assets
    def find_asset_url(condition):
      try:
        return next(asset['browser_download_url'] for asset in assets if condition(asset))
      except StopIteration:
        return None
    
    download_urls = {
      'Windows': find_asset_url(lambda asset: 'Windows' in asset['name'] and '.exe' in asset['name']),
      'Linux': find_asset_url(lambda asset: 'Ubuntu' in asset['name'] and '.AppImage' in asset['name']),
      'Darwin': find_asset_url(lambda asset: 'OSX' in asset['name'] and '.zip' in asset['name']),
    }
    
    # Remove None values (assets that don't exist)
    download_urls = {k: v for k, v in download_urls.items() if v is not None}
    
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
    self.add_log(f'Extracting {zip_path} to {extract_to}')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
      zip_ref.extractall(extract_to)
    self.add_log(f'Extraction complete')


  def _replace_executable(self, download_path, executable_name):
    current_executable = sys.executable
    if current_executable.endswith('python.exe') or current_executable.endswith('python'):
      raise Exception('Cannot replace the current executable as it is running in a virtual environment.')
    
    self.add_log(f'Preparing executable replacement of: {current_executable}')
    
    if sys.platform == "win32":
      # For Windows, directly replace the .exe file
      new_executable = download_path
      current_folder = os.path.dirname(current_executable)
      executable_basename = os.path.basename(current_executable)
      
      # Check if the target directory needs admin privileges
      requires_admin = any(folder in current_folder.lower() for folder in ['program files', 'program files (x86)', 'windows', 'system32'])
      
      # Create a batch script to replace the executable after the current process exits
      script_path = os.path.join(os.path.dirname(download_path), 'replace_executable.bat')
      
      self.add_log(f"Executable to replace: {executable_basename} in {current_folder}", debug=True)
      
      # Use copy for direct file replacement
      copy_cmd = f'copy /Y /B "{new_executable}" "{current_executable}"'
      
      self.add_log(f"Copy command: {copy_cmd}", debug=True)
      self.add_log(f"Creating update script: {script_path}", debug=True)
      
      # Create the batch file with proper admin elevation
      with open(script_path, 'w') as script:
        # Add UAC elevation script for admin privileges
        if requires_admin:
          script.write(f"""@echo off
echo EdgeNodeLauncher Update Process
echo ========================================
echo Starting update process...
echo NOTE: Docker containers will continue running during update
echo Waiting for application to close...

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

:: Wait for the application to close with extended timeout
set MAX_WAIT=30
set COUNTER=0

:loop
tasklist /FI "IMAGENAME eq {executable_basename}" 2>NUL | find /I /C "{executable_basename}" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Process {executable_basename} is still running... (%COUNTER%/%MAX_WAIT% seconds)
    set /a COUNTER+=1
    if %COUNTER% GEQ %MAX_WAIT% (
        echo Process wait timeout reached. Attempting to terminate process...
        taskkill /F /IM "{executable_basename}" 2>NUL
        timeout /T 3 /NOBREAK >NUL
        goto proceed
    )
    timeout /T 1 /NOBREAK >NUL
    goto loop
)

:proceed
echo Application closed or terminated. 
echo Copying new executable to {current_folder}...

:: Give it a moment to fully release files
timeout /T 3 /NOBREAK >NUL

:: Create a backup of the current executable
echo Creating backup of current executable...
if exist "{current_executable}" (
    copy /Y /B "{current_executable}" "{current_executable}.bak"
    if %errorlevel% neq 0 (
        echo Failed to create backup. Aborting update.
        pause
        goto exit_script
    )
)

:: Copy the new executable
echo Running: {copy_cmd}
{copy_cmd}
if %errorlevel% neq 0 (
    echo Copy failed with code: %errorlevel%
    if exist "{current_executable}.bak" (
        echo Restoring from backup...
        copy /Y /B "{current_executable}.bak" "{current_executable}"
    )
    echo Update failed. Please try again or contact support.
    pause
    goto exit_script
)

:: Make sure the executable has the right permissions
echo Setting permissions...
icacls "{current_executable}" /grant Everyone:F >NUL 2>&1

:: Remove backup if update was successful
if exist "{current_executable}.bak" (
    del "{current_executable}.bak" >NUL 2>&1
)

echo Update successful. Launching application...
timeout /T 2 /NOBREAK >NUL
cd /D "{current_folder}"
start "" "{current_executable}"

:exit_script
echo Cleaning up...
:: Delete the temporary files
if exist "{new_executable}" del "{new_executable}" >NUL 2>&1
echo Done.
:: Delete the batch file and close the window
(goto) 2>nul & del "%~f0" & exit
""")
        else:
          # Regular non-admin script for user directories
          script.write(f"""@echo off
echo EdgeNodeLauncher Update Process
echo ========================================
echo Starting update process...
echo NOTE: Docker containers will continue running during update
echo Waiting for application to close...

:: Wait for the application to close with extended timeout
set MAX_WAIT=30
set COUNTER=0

:loop
tasklist /FI "IMAGENAME eq {executable_basename}" 2>NUL | find /I /C "{executable_basename}" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Process {executable_basename} is still running... (%COUNTER%/%MAX_WAIT% seconds)
    set /a COUNTER+=1
    if %COUNTER% GEQ %MAX_WAIT% (
        echo Process wait timeout reached. Attempting to terminate process...
        taskkill /F /IM "{executable_basename}" 2>NUL
        timeout /T 3 /NOBREAK >NUL
        goto proceed
    )
    timeout /T 1 /NOBREAK >NUL
    goto loop
)

:proceed
echo Application closed or terminated.
echo Copying new executable to {current_folder}...

:: Give it a moment to fully release files
timeout /T 3 /NOBREAK >NUL

:: Create a backup of the current executable
echo Creating backup of current executable...
if exist "{current_executable}" (
    copy /Y /B "{current_executable}" "{current_executable}.bak"
    if %errorlevel% neq 0 (
        echo Failed to create backup. Aborting update.
        pause
        goto exit_script
    )
)

:: Copy the new executable
echo Running: {copy_cmd}
{copy_cmd}
if %errorlevel% neq 0 (
    echo Copy failed with code: %errorlevel%
    if exist "{current_executable}.bak" (
        echo Restoring from backup...
        copy /Y /B "{current_executable}.bak" "{current_executable}"
    )
    echo Update failed. Please try again or contact support.
    pause
    goto exit_script
)

:: Remove backup if update was successful
if exist "{current_executable}.bak" (
    del "{current_executable}.bak" >NUL 2>&1
)

echo Update successful. Launching application...
timeout /T 2 /NOBREAK >NUL
cd /D "{current_folder}"
start "" "{current_executable}"

:exit_script
echo Cleaning up...
:: Delete the temporary files
if exist "{new_executable}" del "{new_executable}" >NUL 2>&1
echo Done.
:: Delete the batch file and close the window
(goto) 2>nul & del "%~f0" & exit
""")

      # Execute the batch script with a visible window for better user feedback
      self.add_log(f'Batch script created: {script_path}')
      
      # Run the updater script with a visible console window so user can see progress
      self.add_log(f'Executing updater script: {script_path}')
      
      # Start the script in a new console window that shows progress
      if requires_admin:
          # For admin scripts, we need to show the UAC prompt and console window
          subprocess.Popen(["cmd", "/c", f'title "EdgeNodeLauncher Update" && "{script_path}" && pause'], 
                          shell=True,
                          creationflags=subprocess.CREATE_NEW_CONSOLE)
      else:
          # For non-admin scripts, show in new console window
          subprocess.Popen(["cmd", "/c", f'title "EdgeNodeLauncher Update" && "{script_path}" && pause'], 
                          shell=True,
                          creationflags=subprocess.CREATE_NEW_CONSOLE)

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

    # Schedule application exit after a short delay to ensure UI updates are processed
    from PyQt5.QtCore import QTimer
    
    def delayed_exit():
        """Exit the application after ensuring all UI operations are complete"""
        try:
            # Get the application instance
            app = QApplication.instance()
            
            # First attempt: Graceful close
            if app:
                self.add_log("Attempting graceful application shutdown...", debug=True)
                app.closeAllWindows()
                app.processEvents()
                
                # Give a brief moment for graceful shutdown
                import time
                time.sleep(0.5)
                app.processEvents()
            
            # Second attempt: Force quit with basic cleanup
            self.add_log("Forcing application exit for update...", debug=True)
            
            # Stop only GUI timers (monitoring will stop naturally)
            try:
                # Stop timers if they exist
                if hasattr(self, 'timer') and self.timer:
                    self.timer.stop()
            except:
                pass
            
            # Third attempt: System exit
            try:
                if app:
                    app.quit()
                    app.processEvents()
                sys.exit(0)
            except:
                pass
                
        except:
            pass
        
        # Final fallback: Force exit at OS level (only the GUI process)
        try:
            import os
            self.add_log("Using OS-level force exit for GUI application", debug=True)
            if os.name == 'nt':  # Windows
                # On Windows, use taskkill to force close only our GUI process
                import subprocess
                current_pid = os.getpid()
                try:
                    # Kill only the current GUI process
                    subprocess.run(['taskkill', '/F', '/PID', str(current_pid)], 
                                 capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except:
                    pass
            # Fallback for all platforms
            os._exit(0)
        except:
            # Last resort - this should never fail
            import signal
            os.kill(os.getpid(), signal.SIGTERM)
    
    # Show message to user
    QMessageBox.information(None, 'Update Ready', 
                           'The update has been prepared. The application will now close and update itself.\n\n' +
                           'Please do not close the update window that appears.')
    
    # Schedule delayed exit to allow message box to close properly
    QTimer.singleShot(1000, delayed_exit)
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
            # Get download URL based on platform
            download_url = download_urls.get(platform_system)
            
            if not download_url:
              self.add_log(f"No download URL available for platform: {platform_system}")
              QMessageBox.information(None, 'Update Not Available', f'No update available for your OS: {platform_system}.')
              return
              
          except Exception as e:
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
                self._extract_zip(downloaded_file, os.path.dirname(downloaded_file))
            
            # Show final confirmation before proceeding with update
            reply = QMessageBox.question(None, 'Ready to Update', 
                                       'The update has been downloaded and is ready to install.\n\n' +
                                       'The application will close and update itself automatically.\n' +
                                       'This process may take 30-60 seconds.\n\n' +
                                       'Do you want to proceed with the update now?',
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
              # Replace the executable
              self._replace_executable(downloaded_file, 'EdgeNodeLauncher')
            else:
              self.add_log("Update cancelled by user")
              QMessageBox.information(None, 'Update Cancelled', 'The update has been cancelled. You can update later from the menu.')
          except Exception as e:
            self.add_log(f"Error during download or installation: {str(e)}")
            QMessageBox.critical(None, 'Update Failed', f'Failed to download or install the update: {str(e)}')
      else:
        if verbose:
          self.add_log("You are already using the latest version. Current: {}, Online: {}".format(CURRENT_VERSION, latest_version))
    except Exception as e:
      self.add_log(f"Failed to check for updates: {e}")
