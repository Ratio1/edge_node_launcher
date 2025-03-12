import os
import sys
import requests
import zipfile
import shutil
import platform
import subprocess
from PyQt5.QtWidgets import QMessageBox

from ver import __VER__ as CURRENT_VERSION

GITHUB_API_URL = 'https://api.github.com/repos/Ratio1/edge_node_launcher/releases/latest'
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
      'Windows': next(asset['browser_download_url'] for asset in assets if 'WIN32' in asset['name']),
      'Linux_Ubuntu_24.04': next(asset['browser_download_url'] for asset in assets if 'Ubuntu-24.04' in asset['name']),
      'Linux_Ubuntu_22.04': next(asset['browser_download_url'] for asset in assets if 'Ubuntu-22.04' in asset['name']),
      'Linux_Ubuntu_20.04': next(asset['browser_download_url'] for asset in assets if 'Ubuntu-20.04' in asset['name']),
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

  @staticmethod
  def _download_update(download_url, download_dir):
    os.makedirs(download_dir, exist_ok=True)
    local_filename = os.path.join(download_dir, 'update.zip')
    with requests.get(download_url, stream=True) as response:
      response.raise_for_status()
      with open(local_filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
          file.write(chunk)
    return local_filename

  @staticmethod
  def _extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
      zip_ref.extractall(extract_to)


  def _replace_executable(self, extracted_dir, executable_name):
    current_executable = sys.executable
    if current_executable.endswith('python.exe'):
      raise Exception('Cannot replace the current executable as it is running in a virtual environment.')
    
    self.add_log(f'Preparing executable replacement of: {current_executable}')
    
    if sys.platform == "win32":
      new_executable = os.path.join(extracted_dir, executable_name + '.exe')
      current_folder = os.path.dirname(current_executable)
      temp_executable = os.path.join(current_folder, executable_name + '_new.exe')

      # Copy the new executable to a temporary location
      shutil.copy(new_executable, temp_executable)
      self.add_log(f'New executable copied to temporary location: {temp_executable}')

      # Create a batch script to replace the executable after the current process exits
      script_path = os.path.join(extracted_dir, 'replace_executable.bat')
      move_cmd = f'move /Y "{temp_executable}" "{current_executable}"'
      self.add_log("Move command: " + move_cmd, debug=True)
      self.add_log("Executing script: " + script_path, debug=True)
      with open(script_path, 'w') as script:
        script.write(f"""
        @echo off
        :loop
        tasklist /FI "IMAGENAME eq {os.path.basename(current_executable)}" 2>NUL | find /I /N "{os.path.basename(current_executable)}">NUL
        if "%ERRORLEVEL%"=="0" (
            timeout /T 1 /NOBREAK >NUL
            goto loop
        )
        {move_cmd}
        timeout /T 5 /NOBREAK >NUL
        start "" "{current_executable}"
        """)

      # Execute the batch script
      if os.name == 'nt':
        subprocess.Popen(['cmd', '/c', 'start', '/min', script_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
      else:
        subprocess.Popen(['cmd', '/c', 'start', '/min', script_path], shell=True)
      self.add_log(f'Batch script created and executed: {script_path}')

    else:
      new_executable = os.path.join(extracted_dir, executable_name)
      temp_executable = os.path.join(extracted_dir, executable_name + '_new')

      # Copy the new executable to a temporary location
      shutil.copy(new_executable, temp_executable)
      self.add_log(f'New executable copied to temporary location: {temp_executable}')

      # Create a shell script to replace the executable after the current process exits
      script_path = os.path.join(extracted_dir, 'replace_executable.sh')
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
              QMessageBox.information(None, 'Update Not Available', f'No update available for your OS: {platform_system}.')
              return
          else:
            QMessageBox.information(None, 'Update Not Available', f'No update available for your OS: {platform_system}.')
            return
          download_dir = os.path.join(os.getcwd(), DOWNLOAD_DIR)
          self.add_log(f'Downloading update from {download_url} to {download_dir}...'                       )
          zip_path = self._download_update(download_url, download_dir)
          self.add_log(f'Extracting update from {zip_path}...')
          self._extract_zip(zip_path, download_dir)
          self._replace_executable(download_dir, 'EdgeNodeLauncher')
      else:
        if verbose:
          self.add_log("You are already using the latest version. Current: {}, Online: {}".format(CURRENT_VERSION, latest_version))
    except Exception as e:
      self.add_log(f"Failed to check for updates: {e}")

