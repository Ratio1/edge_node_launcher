import os
import sys
import platform
import subprocess
import platform
import base64

from pathlib import Path
from collections import OrderedDict
from time import sleep
from uuid import uuid4

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QDialog, QInputDialog, QLabel,
                             QMessageBox, QProgressBar, QTextEdit, QVBoxLayout)

from .const import *
from .docker_commands import DockerCommandHandler
from .ssh_service import SSHService, SSHConfig
from .service_manager import ServiceManager
from widgets.dialogs.DockerCheckDialog import DockerCheckDialog

def get_user_folder():
  """
  Returns the user folder.
  """
  return Path.home() / HOME_SUBFOLDER

class DockerPullThread(QThread):
  progress_update = pyqtSignal(str, int)
  pull_finished = pyqtSignal(bool)

  def __init__(self, docker_pull_command):
    super().__init__()
    self.docker_pull_command = docker_pull_command
    self.total_layers = 0
    self.pulled_layers = 0    
    return


  def run(self):
    try:
      docker_pull_command = self.docker_pull_command    
      if os.name == 'nt':
        process = subprocess.Popen(docker_pull_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
      else:
        process = subprocess.Popen(docker_pull_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

      for line in iter(process.stdout.readline, ''):
        self.parse_output(line)
        self.progress_update.emit(line.strip(), self.calculate_progress())
      
      process.stdout.close()
      process.wait()

      if process.returncode == 0:
        self.pull_finished.emit(True)
      else:
        self.pull_finished.emit(False)

    except subprocess.CalledProcessError:
      self.pull_finished.emit(False)
    return


  def parse_output(self, line):    
    DONE = [
      'Image is up to date',
      'Pull complete',
      'Already exists',
    ]
    START = [
      'Already exists',
      'Pulling fs layer',
      'Image is up to date',
    ]
    for d in DONE:
      if d in line:
        self.pulled_layers += 1
    for s in START:
      if s in line:
        self.total_layers += 1
    return


  def calculate_progress(self):
    if self.total_layers == 0:
      return 0
    return int((self.pulled_layers / self.total_layers) * 100)
  


class ProgressBarWindow(QDialog):
  def __init__(self, message, icon_object, sender):
    super().__init__()
    self.sender = sender
    self.setWindowTitle("Progress")
    self.setWindowIcon(icon_object)
    self.setWindowModality(Qt.ApplicationModal)
    self.setGeometry(300, 300, 600, 400)  # Larger size
    layout = QVBoxLayout()

    self.label = QLabel(message)
    layout.addWidget(self.label)

    self.output_edit = QTextEdit()
    self.output_edit.setReadOnly(True)
    layout.addWidget(self.output_edit)

    self.progress_bar = QProgressBar(self)
    self.progress_bar.setMaximum(100)
    layout.addWidget(self.progress_bar)

    self.setLayout(layout)
    self.apply_stylesheet()
    
    screen_geometry = QApplication.desktop().screenGeometry()
    x = (screen_geometry.width() - self.width()) // 2
    y = (screen_geometry.height() - self.height()) // 2
    self.move(x, y)
    return
  
  
  def update_progress(self, output, progress):
    self.output_edit.append(output)
    self.output_edit.verticalScrollBar().setValue(self.output_edit.verticalScrollBar().maximum())
    self.progress_bar.setValue(progress)


  def apply_stylesheet(self):
    self.setStyleSheet(self.sender._current_stylesheet)
    return

  
  def on_docker_pull_finished(self, success):
    if success:
      QMessageBox.information(self, 'Docker Pull', 'Docker image pulled successfully.')      
      self.sender.add_log('Docker image pulled successfully.')
    else:
      QMessageBox.warning(self, 'Docker Pull', 'Failed to pull Docker image.\nCheck if Docker is running.')
    self.accept()  # Close the progress dialog
    return



class _DockerUtilsMixin:
  def __init__(self):
    super().__init__()
    
    self.init_directories()
    
    self.docker_commands = DockerCommandHandler(DOCKER_CONTAINER_NAME)
    self.ssh_service = SSHService()
    self.service_manager = ServiceManager(self.ssh_service)

    self.node_addr = None
    self.node_eth_address = None
    self.container_last_run_status = None
    self.docker_container_name = DOCKER_CONTAINER_NAME
    self.docker_tag = DOCKER_TAG
    self.node_id = self.get_node_id()
    self._dev_mode = False
    
    self.run_with_sudo = False
    
    # Remote connection settings
    self.is_remote = False
    self.remote_ssh_command = None
    
    return
  
  def init_directories(self):
    path = get_user_folder()
    path.mkdir(exist_ok=True)
    self.env_file = path / '.env'
    os.chdir(path)
    self.add_log(f'Working directory: {os.getcwd()}')
    return
  
  
  def post_launch_setup(self):
    self.add_log('Executing post-launch setup...')
    return
  
  def docker_initialize(self):
    self._use_gpus = self.check_nvidia_gpu_available()
    self.__generate_env_file()
    self.__setup_docker_run()
    return
  
  def check_nvidia_gpu_available(self):
    result = False
    try:
      if os.name == 'nt':
        output = subprocess.check_output(['nvidia-smi', '-L'], stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
      else:
        output = subprocess.check_output(['nvidia-smi', '-L'], stderr=subprocess.STDOUT, universal_newlines=True)
      result = 'GPU' in output
    except Exception as exc:
      result = False
      output = str(exc)
    output = output.replace('\n', '') 
    self.add_log(f'NVIDIA GPU available: {result} ({output})')
    return result
  
  
  def __setup_docker_run(self):
    self.add_log('Setting up Docker run command...')
    self.docker_image = DOCKER_IMAGE + ":" + self.docker_tag
    
    # Base commands without remote prefix
    base_clean = ['docker', 'rm', self.docker_container_name]
    base_stop = ['docker', 'stop']
    base_inspect = ['docker', 'inspect', '--format', '{{.State.Running}}', self.docker_container_name]
    
    if self._use_gpus:
      str_gpus = '--gpus=all'
      self.add_log('Using GPU.')
    else:
      str_gpus = ''
      self.add_log('Not using GPU.')
    
    base_run = ['docker', 'run']
    if len(str_gpus) > 0:
      base_run += [str_gpus]
    
    if platform.machine() in ['aarch64', 'arm64']:
        base_run += ['--platform', 'linux/amd64']
    
    base_run += [
        '--rm',
        '--gpus', 'all',
        '--env-file', '.env',
        '-v', f'{DOCKER_VOLUME}:/edge_node/_local_cache',
        '--name', self.docker_container_name, '-d',
    ]
    
    # Add sudo if needed
    if self.run_with_sudo:
      base_clean.insert(0, 'sudo')
      base_stop.insert(0, 'sudo')
      base_inspect.insert(0, 'sudo')
      base_run.insert(0, 'sudo')
    
    # Add remote prefix if needed
    if self.is_remote and self.remote_ssh_command:
      self.__CMD_CLEAN = self.remote_ssh_command + base_clean
      self.__CMD_STOP = self.remote_ssh_command + base_stop
      self.__CMD_INSPECT = self.remote_ssh_command + base_inspect
      self.__CMD = self.remote_ssh_command + base_run
    else:
      self.__CMD_CLEAN = base_clean
      self.__CMD_STOP = base_stop
      self.__CMD_INSPECT = base_inspect
      self.__CMD = base_run
    
    run_cmd = " ".join(self.get_cmd())
    
    self.add_log('Docker run command setup complete:')
    self.add_log(f' - Remote mode: {self.is_remote}')
    if self.is_remote:
      self.add_log(f' - SSH command: {" ".join(self.remote_ssh_command)}')
    self.add_log(' - Run:     {}'.format(run_cmd))
    self.add_log(' - Clean:   {}'.format(" ".join(self.__CMD_CLEAN)))
    self.add_log(' - Stop:    {}'.format(" ".join(self.__CMD_STOP)))
    self.add_log(' - Inspect: {}'.format(" ".join(self.__CMD_INSPECT)))
    return
  
  
  def get_cmd(self):
    if self._dev_mode:
      result = self.__CMD + ['-p', '80:80', self.docker_image]
    else:
      result = self.__CMD + [self.docker_image]
    return result
  
  def get_clean_cmd(self):
    return self.__CMD_CLEAN
  
  
  def get_stop_command(self):
    return self.__CMD_STOP
  
  
  def get_inspect_command(self):
    return self.__CMD_INSPECT
  
  
  def __maybe_docker_pull(self):
    architecture = platform.machine()
    docker_pull_command = ['docker', 'pull', self.docker_image]
    if architecture == 'aarch64' or architecture == 'arm64':
      docker_pull_command.insert(2, '--platform')
      docker_pull_command.insert(3, 'linux/amd64')

    str_docker_pull_command = ' '.join(docker_pull_command)
    progress_dialog = ProgressBarWindow(f"Pulling Docker Image: '{str_docker_pull_command}'", self._icon, self)
    self.docker_pull_thread = DockerPullThread(docker_pull_command=docker_pull_command)
    self.docker_pull_thread.progress_update.connect(progress_dialog.update_progress)
    self.docker_pull_thread.pull_finished.connect(progress_dialog.on_docker_pull_finished)
    
    self.docker_pull_thread.start()
    
    self.progress_dialog = progress_dialog
    self.progress_dialog.exec_()
    return
  
  
  def get_node_id(self):
    return 'ratio1_' + str(uuid4())[:8]
  

  def __check_env_keys(self):
    # Load the current .env file
    env_vars = OrderedDict()
    try:
      with open(self.env_file, 'r') as file:
        for line in file:
          if line.strip() and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            env_vars[key] = value
    except FileNotFoundError:
      QMessageBox.warning(self, 'Error', '.env file not found.')
      return False
    return True
    
    
  def __generate_env_file(self):
    self.add_log(f'Checking {self.env_file} file...')
    if os.path.exists(self.env_file):
      pass
    else:
      str_env = ENV_TEMPLATE.format(
        self.node_id, 
      )
      with open(self.env_file, 'w') as f:
        f.write(str_env)    
    return

  def check_docker(self):
    """Check if Docker is installed and running.
    
    Returns:
        tuple: (is_installed, is_running, error_message)
            - is_installed: bool indicating if Docker is installed
            - is_running: bool indicating if Docker daemon is running
            - error_message: str with error details if any, None otherwise
    """
    self.add_log('Checking Docker status...')
    try:
        # First check if Docker is installed
        if os.name == 'nt':
            output = subprocess.check_output(['docker', '--version'], stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            output = subprocess.check_output(['docker', '--version'], stderr=subprocess.STDOUT, universal_newlines=True)
        self.add_log("Docker version: " + output.strip())
        
        # Then check if Docker daemon is running
        if os.name == 'nt':
            subprocess.check_output(['docker', 'info'], stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.check_output(['docker', 'info'], stderr=subprocess.STDOUT, universal_newlines=True)
        
        self.add_log("Docker daemon is running")
        return True, True, None
    except FileNotFoundError:
        return False, False, "Docker is not installed"
    except subprocess.CalledProcessError:
        return True, False, "Docker daemon is not running"


  def is_container_running(self):
    try:
      inspect_cmd = self.get_inspect_command()
      if os.name == 'nt':
        status = subprocess.check_output(inspect_cmd, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
      else:
        status = subprocess.check_output(inspect_cmd, stderr=subprocess.STDOUT, universal_newlines=True)

      status = status.strip()
      container_running = status.split()[-1] == 'true'
      if container_running != self.container_last_run_status:
        self.add_log('Edge Node container status changed: {} -> {} (status: {})'.format(
          self.container_last_run_status, container_running, status
        ))
        self.container_last_run_status = container_running
        if container_running:
          self.post_launch_setup()
      return container_running
    except:
      return False


  def launch_container(self):
    # Check Docker status first
    if not self.check_docker():
        return

    is_env_ok = self.__check_env_keys()
    if not is_env_ok:
        self.add_log('Environment is not ok. Could not start the container.')
        return

    # If in multi-host mode, use the service command instead
    if self.is_remote:
        try:
            self.add_log('Starting Edge Node service on remote host...')
            
            success, error = self.service_manager.restart_service('mnl_execution_engine')
            
            if not success:
                raise Exception(error)
            
            self.add_log('Edge Node service restarted successfully.')
            QMessageBox.information(self, 'Service Restart', 'Edge Node service restarted successfully.')
            self.post_launch_setup()
            return
            
        except Exception as e:
            QMessageBox.warning(self, 'Service Restart', 'Failed to restart Edge Node service')
            self.add_log(f'Edge Node service restart failed: {str(e)}')
            return

    # Regular Docker container launch for local mode
    self.add_log('Updating image...')
    self.__maybe_docker_pull()
    # first try to clean the container
    self.add_log("Attempting to clean up the container...")
    clean_cmd = self.get_clean_cmd()
    try:
      if os.name == 'nt':
        # subprocess.call(clean_cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        output = subprocess.check_output(
          clean_cmd, 
          stderr=subprocess.STDOUT, 
          universal_newlines=True, 
          creationflags=subprocess.CREATE_NO_WINDOW
        )
      else:
        output = subprocess.check_output(
          clean_cmd, 
          stderr=subprocess.STDOUT
        )
      # endif windows or not
      self.add_log('Container cleanup status: {}'.format(output))
    except subprocess.CalledProcessError as e:
      error_code = e.returncode
      error_output = e.output
      self.add_log('Edge Node container cleanup failed with code={}: {}'.format(error_code, error_output))
    except Exception as e:
      self.add_log('Edge Node container cleanup failed with unknown error: {}'.format(e))
    
    try:
      self.add_log('Starting Edge Node container...')
      run_cmd = self.get_cmd()
      if os.name == 'nt':
        # rc = subprocess.call(run_cmd, creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
        output = subprocess.check_output(
          run_cmd, 
          stderr=subprocess.STDOUT, 
          universal_newlines=True, 
          creationflags=subprocess.CREATE_NO_WINDOW
        )
      else:
        # rc = subprocess.call(run_cmd, timeout=20)
        output = subprocess.check_output(
          run_cmd, 
          stderr=subprocess.STDOUT, 
        )
      # endif windows or not
      self.add_log('Container start status: {}'.format(output))
      QMessageBox.information(self, 'Container Launch', 'Container launched successfully.')
      self.add_log('Edge Node container launched successfully.')
      self.post_launch_setup()
      # endif container running
    except subprocess.CalledProcessError as e:
      error_code = e.returncode
      error_output = e.output
      QMessageBox.warning(self, 'Container Launch', 'Failed to launch container')
      self.add_log('Edge Node container start failed with error code={}: {}'.format(error_code, error_output))
    except Exception as e:
      QMessageBox.warning(self, 'Container Launch', 'Failed to launch container')
      self.add_log('Edge Node container start failed with unknown error: {}'.format(e))
    return


  def stop_container(self, container_name=None):
    try:
      name_to_stop = container_name or self.docker_container_name
      self.add_log(f'Stopping Edge Node container {name_to_stop}...')
      stop_cmd = self.get_stop_command() + [name_to_stop]  # Append container name to stop command
      
      if os.name == 'nt':
        subprocess.check_call(stop_cmd, creationflags=subprocess.CREATE_NO_WINDOW)
      else:
        subprocess.check_call(stop_cmd)
      sleep(2)
      QMessageBox.information(self, 'Container Stop', 'Container stopped successfully.')      
      self.add_log('Edge Node container stopped successfully.')
      try:
        self.add_log('Cleaning Edge Node container...')
        clean_cmd = self.get_clean_cmd()
        if container_name:
          # Replace the default container name with the provided one
          clean_cmd = clean_cmd[:-1] + [name_to_stop]
        if os.name == 'nt':
          subprocess.check_call(clean_cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
          subprocess.check_call(clean_cmd)
        self.add_log('Edge Node container removed.')
      except subprocess.CalledProcessError:
        self.add_log('Edge Node container removal failed probably due to already being removed.')
    except subprocess.CalledProcessError:
      QMessageBox.warning(self, 'Container Stop', 'Failed to stop container.')
      self.add_log('Edge Node container stop failed.')
    return


  def set_remote_connection(self, ssh_command: str):
    """Set up remote connection using SSH command."""
    if not ssh_command:
      self.clear_remote_connection()
      return

    # Get current host configuration
    current_host = self.host_selector.get_current_host()
    host_config = self.host_selector.hosts_manager.get_host(current_host)
    
    if not host_config:
      return

    # Configure SSH service
    ssh_config = SSHConfig(
      host=host_config.ansible_host,
      user=host_config.ansible_user,
      password=host_config.ansible_become_password,
      private_key=host_config.ansible_ssh_private_key_file,
      ssh_args=host_config.ansible_ssh_common_args.split() if host_config.ansible_ssh_common_args else None
    )
    
    self.ssh_service.configure(ssh_config)
    
    # Update Docker settings
    self.is_remote = True
    self.remote_ssh_command = ssh_command.split()
    self.__setup_docker_run()
    
    # Update Docker command handler
    self.docker_commands.set_remote_connection(ssh_command)

  def clear_remote_connection(self):
    """Clear remote connection settings."""
    self.is_remote = False
    self.remote_ssh_command = None
    self.ssh_service.clear_configuration()
    self.docker_commands.clear_remote_connection()
    self.__setup_docker_run()
  