import os
import json
import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import logging
import platform

from models.NodeInfo import NodeInfo
from models.NodeHistory import NodeHistory
from models.StartupConfig import StartupConfig
from models.ConfigApp import ConfigApp
from utils.const import DOCKER_VOLUME_PATH

# Docker configuration
DOCKER_IMAGE = "ratio1/edge_node:mainnet"
DOCKER_TAG = "latest"

@dataclass
class ContainerInfo:
    """Container information storage class"""
    container_name: str
    volume_name: str
    created_at: str
    last_used: str

class ContainerRegistry:
    """Manages persistence of container and volume information"""
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser("~/.edge_node/containers.json")
        self._ensure_storage_exists()
        self.containers: Dict[str, ContainerInfo] = self._load_containers()

    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory and file exist"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            self._save_containers({})

    def _load_containers(self) -> Dict[str, ContainerInfo]:
        """Load containers from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return {
                    name: ContainerInfo(**info) 
                    for name, info in data.items()
                }
        except Exception:
            return {}

    def _save_containers(self, containers: dict) -> None:
        """Save containers to storage"""
        with open(self.storage_path, 'w') as f:
            json.dump(containers, f, indent=2)

    def add_container(self, container_name: str, volume_name: str) -> None:
        """Add a new container to registry"""
        now = datetime.now().isoformat()
        self.containers[container_name] = ContainerInfo(
            container_name=container_name,
            volume_name=volume_name,
            created_at=now,
            last_used=now
        )
        self._save_containers({
            name: vars(info)
            for name, info in self.containers.items()
        })

    def remove_container(self, container_name: str) -> None:
        """Remove a container from registry"""
        if container_name in self.containers:
            del self.containers[container_name]
            self._save_containers({
                name: vars(info)
                for name, info in self.containers.items()
            })

    def get_container_info(self, container_name: str) -> Optional[ContainerInfo]:
        """Get container information"""
        return self.containers.get(container_name)

    def get_volume_name(self, container_name: str) -> Optional[str]:
        """Get volume name for container"""
        info = self.get_container_info(container_name)
        return info.volume_name if info else None

    def update_last_used(self, container_name: str) -> None:
        """Update last used timestamp for container"""
        if container_name in self.containers:
            self.containers[container_name].last_used = datetime.now().isoformat()
            self._save_containers({
                name: vars(info)
                for name, info in self.containers.items()
            })

    def list_containers(self) -> List[ContainerInfo]:
        """List all registered containers"""
        return list(self.containers.values())

class DockerCommandThread(QThread):
    """ Thread to run a Docker command """
    command_finished = pyqtSignal(dict)
    command_error = pyqtSignal(str)

    def __init__(self, container_name: str, command: str, input_data: str = None, remote_ssh_command: list = None):
        super().__init__()
        self.container_name = container_name
        self.command = command
        self.input_data = input_data
        self.remote_ssh_command = remote_ssh_command

    def run(self):
        try:
            full_command = ['docker', 'exec']
            if self.input_data is not None:
                full_command.extend(['-i'])  # Add interactive flag when input is provided
            full_command.extend([self.container_name] + self.command.split())

            # Add remote prefix if needed
            if self.remote_ssh_command:
                full_command = self.remote_ssh_command + full_command
                
            # Always log the command before executing it
            logging.info(f"Executing command: {' '.join(full_command)}")
            if self.input_data:
                logging.info(f"With input data: {self.input_data[:100]}{'...' if len(self.input_data) > 100 else ''}")

            # Use a longer timeout for remote commands
            timeout = 20 if self.remote_ssh_command else 10  # Increased timeout for remote commands

            try:
                if os.name == 'nt':
                    result = subprocess.run(
                        full_command,
                        input=self.input_data,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    result = subprocess.run(
                        full_command,
                        input=self.input_data,
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                if result.returncode != 0:
                    self.command_error.emit(f"Command failed: {result.stderr}\nCommand: {' '.join(full_command)}\nInput data: {self.input_data}")
                    return
                
                # If command is reset_address or change_alias, process output as plain text
                if self.command == 'reset_address' or self.command.startswith('change_alias'):
                    self.command_finished.emit({'message': result.stdout.strip()})
                    return
                
                try:
                    data = json.loads(result.stdout)
                    self.command_finished.emit(data)
                except json.JSONDecodeError:
                    self.command_error.emit(f"Error decoding JSON response. Raw output: {result.stdout}")
                except Exception as e:
                    self.command_error.emit(f"Error processing response: {str(e)}\nRaw output: {result.stdout}")
            except subprocess.TimeoutExpired as e:
                error_msg = f"Command timed out after {e.timeout} seconds: {' '.join(full_command)}"
                print(error_msg)
                if hasattr(e, 'stdout') and e.stdout:
                    print(f"  stdout: {e.stdout}")
                if hasattr(e, 'stderr') and e.stderr:
                    print(f"  stderr: {e.stderr}")
                self.command_error.emit(error_msg)
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}\nCommand: {' '.join(full_command) if 'full_command' in locals() else self.command}\nInput data: {self.input_data}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.command_error.emit(error_msg)

class DockerCommandHandler:
    """ Handles Docker commands """
    def __init__(self, container_name: str = None):
        """Initialize the handler.
        
        Args:
            container_name: Name of container to manage
        """
        self.container_name = container_name
        self.registry = ContainerRegistry()
        self._debug_mode = False
        self.threads = []
        self.remote_ssh_command = None

    def set_debug_mode(self, enabled: bool) -> None:
        """Set debug mode for docker commands.
        
        Args:
            enabled: Whether to enable debug mode
        """
        self._debug_mode = enabled

    def set_container_name(self, container_name: str):
        """Set the container name."""
        self.container_name = container_name

    def execute_command(self, command: list) -> tuple:
        """Execute a docker command.
        
        Args:
            command: Command to execute as list of strings
            
        Returns:
            tuple: (stdout, stderr, return_code)
        """
        try:
            if self._debug_mode:
                print(f"Executing command: {' '.join(command)}")
                
            result = subprocess.run(command, capture_output=True, text=True)
            
            if self._debug_mode and result.returncode != 0:
                print(f"Command failed with code {result.returncode}")
                print(f"stderr: {result.stderr}")
                
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            if self._debug_mode:
                print(f"Command execution failed: {str(e)}")
            return "", str(e), 1

    def _ensure_image_exists(self, callback=None, error_callback=None) -> None:
        """Check if the Docker image exists locally and pull it if not.
        
        Args:
            callback: Function to call on success
            error_callback: Function to call on error
        """
        # If callbacks are provided, run in a thread
        if callback or error_callback:
            thread = QThread()
            
            def run_ensure_image():
                try:
                    # Check if image exists
                    command = ['docker', 'images', '-q', DOCKER_IMAGE]
                    stdout, stderr, return_code = self.execute_command(command)
                    
                    if not stdout.strip():  # Image doesn't exist
                        # Image doesn't exist, try to pull it
                        pull_command = ['docker', 'pull', DOCKER_IMAGE]
                        stdout, stderr, return_code = self.execute_command(pull_command)
                        
                        if return_code != 0:
                            raise Exception(f"Failed to pull Docker image: {stderr}")
                    
                    # Call success callback if provided
                    if callback:
                        self._invoke_callback(callback)
                except Exception as e:
                    logging.error(f"Error ensuring image exists: {str(e)}")
                    if error_callback:
                        self._invoke_callback(error_callback, str(e))
            
            # Connect thread
            thread.run = run_ensure_image
            thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
            self.threads.append(thread)
            thread.start()
            return None
        else:
            # Run synchronously
            # Check if image exists
            command = ['docker', 'images', '-q', DOCKER_IMAGE]
            stdout, stderr, return_code = self.execute_command(command)
            
            if stdout.strip():  # Image exists
                return True
                
            # Image doesn't exist, try to pull it
            pull_command = ['docker', 'pull', DOCKER_IMAGE]
            stdout, stderr, return_code = self.execute_command(pull_command)
            
            if return_code != 0:
                raise Exception(f"Failed to pull Docker image: {stderr}")
                
            return True

    def check_and_pull_image_updates(self, image_name: str = None, tag: str = None, callback=None, error_callback=None) -> None:
        """Check if a Docker image has updates available and pull if it does.
        
        Args:
            image_name: Docker image name (defaults to DOCKER_IMAGE)
            tag: Docker image tag (defaults to DOCKER_TAG)
            callback: Function to call with results (was_updated, message)
            error_callback: Function to call on error
        """
        # If callbacks provided, run asynchronously
        if callback:
            thread = QThread()
            
            def run_check_update():
                try:
                    # Use default if not specified
                    img_name = image_name or DOCKER_IMAGE
                    img_tag = tag or DOCKER_TAG
                    
                    full_image_name = f"{img_name}:{img_tag}"
                    
                    # Check if an update is available
                    check_cmd = ['docker', 'pull', '--quiet', full_image_name]
                    stdout, stderr, return_code = self.execute_command(check_cmd)
                    
                    # If we got output and command was successful, an update is available
                    if return_code == 0 and stdout.strip() and "Image is up to date" not in stderr:
                        # Pull the updated image
                        pull_cmd = ['docker', 'pull', full_image_name]
                        pull_stdout, pull_stderr, pull_return_code = self.execute_command(pull_cmd)
                        
                        if pull_return_code == 0:
                            result = (True, f"Docker image {full_image_name} updated successfully")
                        else:
                            result = (False, f"Failed to update Docker image: {pull_stderr}")
                    else:
                        result = (False, f"No updates available for Docker image {full_image_name}")
                    
                    # Call success callback with results
                    self._invoke_callback(callback, result)
                except Exception as e:
                    logging.error(f"Error checking for image updates: {str(e)}")
                    if error_callback:
                        self._invoke_callback(error_callback, str(e))
            
            # Connect thread
            thread.run = run_check_update
            thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
            self.threads.append(thread)
            thread.start()
        else:
            # Use default if not specified
            img_name = image_name or DOCKER_IMAGE
            img_tag = tag or DOCKER_TAG
            
            full_image_name = f"{img_name}:{img_tag}"
            
            # Check if an update is available
            check_cmd = ['docker', 'pull', '--quiet', full_image_name]
            stdout, stderr, return_code = self.execute_command(check_cmd)
            
            # If we got output and command was successful, an update is available
            if return_code == 0 and stdout.strip() and "Image is up to date" not in stderr:
                # Pull the updated image
                pull_cmd = ['docker', 'pull', full_image_name]
                pull_stdout, pull_stderr, pull_return_code = self.execute_command(pull_cmd)
                
                if pull_return_code == 0:
                    return (True, f"Docker image {full_image_name} updated successfully")
                else:
                    return (False, f"Failed to update Docker image: {pull_stderr}")
            else:
                return (False, f"No updates available for Docker image {full_image_name}")

    def launch_container(self, volume_name: str = None, callback=None, error_callback=None) -> None:
        """Launch the container with an optional volume.
        
        Args:
            volume_name: Optional volume name to mount
            callback: Function to call on success
            error_callback: Function to call on error
        """
        # Create a thread to run this operation
        thread = QThread()
        
        def run_launch():
            try:
                # We'll handle the image check within this thread
                # Check if a container with the same name already exists
                inspect_command = ['docker', 'container', 'inspect', self.container_name]
                stdout, stderr, return_code = self.execute_command(inspect_command)
                
                # If container exists (return code 0), remove it
                if return_code == 0:
                    remove_command = ['docker', 'rm', '-f', self.container_name]
                    stdout, stderr, return_code = self.execute_command(remove_command)
                    if return_code != 0:
                        raise Exception(f"Failed to remove existing container: {stderr}")
                
                # Check if image exists and pull if needed
                command = ['docker', 'images', '-q', DOCKER_IMAGE]
                stdout, stderr, return_code = self.execute_command(command)
                
                if not stdout.strip():  # Image doesn't exist
                    # Image doesn't exist, try to pull it
                    pull_command = ['docker', 'pull', DOCKER_IMAGE]
                    stdout, stderr, return_code = self.execute_command(pull_command)
                    
                    if return_code != 0:
                        raise Exception(f"Failed to pull Docker image: {stderr}")
                
                # Get the command to run
                command = self.get_launch_command(volume_name)
                
                # Log the full Docker command
                logging.info(f"Launching container with command: {' '.join(command)}")
                
                # Execute the command
                stdout, stderr, return_code = self.execute_command(command)
                if return_code != 0:
                    raise Exception(f"Failed to launch container: {stderr}")

                # Register the container with its volume
                self.registry.add_container(self.container_name, volume_name)
                
                # Log successful launch with volume information
                if volume_name:
                    logging.info(f"Container {self.container_name} launched successfully with volume {volume_name}")
                else:
                    logging.info(f"Container {self.container_name} launched successfully without a specific volume")
                
                # Call success callback if provided
                self._invoke_callback(callback)
            except Exception as e:
                logging.error(f"Error launching container: {str(e)}")
                if error_callback:
                    self._invoke_callback(error_callback, str(e))
        
        # Connect thread
        thread.run = run_launch
        thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
        self.threads.append(thread)
        thread.start()

    def get_launch_command(self, volume_name: str = None) -> list:
        """Get the Docker command that will be used to launch the container.
        
        Args:
            volume_name: Optional volume name to mount
            
        Returns:
            list: The Docker command as a list of strings
        """
        # Base command with container name
        command = [
            'docker', 'run'
        ]
        if platform.machine() in ['aarch64', 'arm64']:
            command += ['--platform', 'linux/amd64']
        command += [
            '-d',  # Run in detached mode
            '--name', self.container_name,  # Set container name
            '--restart', 'unless-stopped',  # Restart policy
        ]
        
        # Add volume mount if specified
        if volume_name:
            command.extend(['-v', f'{volume_name}:{DOCKER_VOLUME_PATH}'])
            logging.info(f"Using volume mount: {volume_name}:{DOCKER_VOLUME_PATH}")
        else:
            logging.warning(f"No volume specified for container {self.container_name}")
        
        # Add the image name from DOCKER_IMAGE constant
        command.append(DOCKER_IMAGE)
        
        return command

    def set_remote_connection(self, ssh_command: str):
        """Set up remote connection using SSH command."""
        self.remote_ssh_command = ssh_command.split() if ssh_command else None

    def clear_remote_connection(self):
        """Clear remote connection settings."""
        self.remote_ssh_command = None

    def _execute_threaded(self, command: str, callback, error_callback, input_data: str = None) -> None:
        thread = DockerCommandThread(self.container_name, command, input_data, self.remote_ssh_command)
        thread.command_finished.connect(callback)
        thread.command_error.connect(error_callback)
        self.threads.append(thread)  # Keep reference to prevent GC
        thread.finished.connect(lambda: self.threads.remove(thread))
        thread.start()

    def get_node_info(self, callback, error_callback) -> None:
        def process_node_info(data: dict):
            try:
                node_info = NodeInfo.from_dict(data)
                callback(node_info)
            except Exception as e:
                error_callback(f"Failed to process node info: {str(e)}")

        self._execute_threaded('get_node_info', process_node_info, error_callback)

    def get_node_history(self, callback, error_callback) -> None:
        def process_metrics(data: dict):
            try:
                metrics = NodeHistory.from_dict(data)
                callback(metrics)
            except Exception as e:
                error_callback(f"Failed to process metrics: {str(e)}")

        self._execute_threaded('get_node_history', process_metrics, error_callback)

    def get_allowed_addresses(self, callback, error_callback) -> None:
        def process_allowed_addresses(output: str):
            try:
                # Convert plain text output to dictionary
                allowed_dict = {}
                for line in output.strip().split('\n'):
                    if line.strip():  # Skip empty lines
                        # Split on '#' and take only the first part
                        main_part = line.split('#')[0].strip()
                        if main_part:  # Skip if line is empty after removing comment
                            address, alias = main_part.split(None, 1)  # Split on whitespace, max 1 split
                            allowed_dict[address] = alias.strip()
                
                callback(allowed_dict)
            except Exception as e:
                error_callback(f"Failed to process allowed addresses: {str(e)}")

        try:
            full_command = ['docker', 'exec', self.container_name, 'get_allowed']
            
            # Add remote prefix if needed
            if self.remote_ssh_command:
                full_command = self.remote_ssh_command + full_command

            if os.name == 'nt':
                result = subprocess.run(
                    full_command,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(full_command, capture_output=True, text=True)

            if result.returncode != 0:
                error_callback(f"Command failed: {result.stderr}")
                return

            process_allowed_addresses(result.stdout)
        except Exception as e:
            error_callback(str(e))

    def update_allowed_batch(self, addresses_data: list, callback, error_callback) -> None:
        """Update allowed addresses in batch
        
        Args:
            addresses_data: List of dicts with 'address' and 'alias' keys
            callback: Success callback
            error_callback: Error callback
        """
        # Format data as one address-alias pair per line
        batch_input = '\n'.join(f"{addr['address']} {addr.get('alias', '')}" 
                              for addr in addresses_data)
        
        self._execute_threaded(
            'update_allowed_batch',  # Just the command name, no data here
            callback,
            error_callback,
            input_data=batch_input + '\n'  # Add final newline and pass as input_data
        )

    def get_startup_config(self, callback, error_callback) -> None:
        def process_startup_config(data: dict):
            try:
                startup_config = StartupConfig.from_dict(data)
                callback(startup_config)
            except Exception as e:
                error_callback(f"Failed to process startup config: {str(e)}")

        self._execute_threaded('get_startup_config', process_startup_config, error_callback)

    def get_config_app(self, callback, error_callback) -> None:
        def process_config_app(data: dict):
            try:
                config_app = ConfigApp.from_dict(data)
                callback(config_app)
            except Exception as e:
                error_callback(f"Failed to process config app: {str(e)}")

        self._execute_threaded('get_config_app', process_config_app, error_callback)

    def reset_address(self, callback, error_callback) -> None:
        """Deletes the E2 PEM file using a Docker command
        
        Args:
            callback: Success callback
            error_callback: Error callback
        """
        def process_response(data: dict):
            try:
                # Extract the message from stdout
                message = data.get('stdout', '').strip()
                callback(message)
            except Exception as e:
                error_callback(f"Failed to process response: {str(e)}")

        self._execute_threaded('reset_address', process_response, error_callback)

    def update_node_name(self, new_name: str, callback, error_callback) -> None:
        """Updates the node name/alias
        
        Args:
            new_name: New name for the node
            callback: Success callback
            error_callback: Error callback
        """
        self._execute_threaded(
            f'change_alias {new_name}',
            callback,
            error_callback
        )

    def stop_container(self, container_name: str = None, callback=None, error_callback=None) -> None:
        """Stop a container.
        
        Args:
            container_name: Name of container to stop. If None, uses self.container_name
            callback: Function to call on success
            error_callback: Function to call on error
        """
        name = container_name or self.container_name
        
        # Create a thread to run this operation
        thread = QThread()
        
        def run_stop():
            try:
                command = ['docker', 'stop', name]
                stdout, stderr, return_code = self.execute_command(command)
                if return_code != 0:
                    raise Exception(f"Failed to stop container {name}: {stderr}")
                
                # Call success callback if provided
                self._invoke_callback(callback)
            except Exception as e:
                logging.error(f"Error stopping container: {str(e)}")
                if error_callback:
                    self._invoke_callback(error_callback, str(e))
        
        # Connect thread
        thread.run = run_stop
        thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
        self.threads.append(thread)
        thread.start()

    def remove_container(self, container_name: str = None, force: bool = False, callback=None, error_callback=None) -> None:
        """Remove a container.
        
        Args:
            container_name: Name of container to remove. If None, uses self.container_name
            force: If True, force remove even if running
            callback: Function to call on success
            error_callback: Function to call on error
        """
        name = container_name or self.container_name
        
        # Create a thread to run this operation
        thread = QThread()
        
        def run_remove():
            try:
                command = ['docker', 'rm']
                if force:
                    command.append('-f')
                command.append(name)
                
                stdout, stderr, return_code = self.execute_command(command)
                if return_code != 0:
                    raise Exception(f"Failed to remove container {name}: {stderr}")

                # Remove from registry
                self.registry.remove_container(name)
                
                # Call success callback if provided
                self._invoke_callback(callback)
            except Exception as e:
                logging.error(f"Error removing container: {str(e)}")
                if error_callback:
                    self._invoke_callback(error_callback, str(e))
        
        # Connect thread
        thread.run = run_remove
        thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
        self.threads.append(thread)
        thread.start()

    def inspect_container(self, container_name: str = None, callback=None, error_callback=None) -> None:
        """Get detailed information about a container.
        
        Args:
            container_name: Name of container to inspect. If None, uses self.container_name
            callback: Function to call with container info
            error_callback: Function to call on error
            
        Returns:
            dict: Container information (only if no callbacks provided)
        """
        name = container_name or self.container_name
        
        # If callbacks provided, run asynchronously
        if callback:
            thread = QThread()
            
            def run_inspect():
                try:
                    command = ['docker', 'inspect', name]
                    stdout, stderr, return_code = self.execute_command(command)
                    
                    if return_code != 0:
                        raise Exception(f"Failed to inspect container {name}: {stderr}")
                        
                    try:
                        container_info = json.loads(stdout)[0]
                        
                        # Call success callback with container info
                        self._invoke_callback(callback, container_info)
                    except (json.JSONDecodeError, IndexError) as e:
                        raise Exception(f"Failed to parse container info: {str(e)}")
                    
                except Exception as e:
                    logging.error(f"Error inspecting container: {str(e)}")
                    if error_callback:
                        self._invoke_callback(error_callback, str(e))
            
            # Connect thread
            thread.run = run_inspect
            thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
            self.threads.append(thread)
            thread.start()
        else:
            # Run synchronously for backwards compatibility
            command = ['docker', 'inspect', name]
            stdout, stderr, return_code = self.execute_command(command)
            if return_code != 0:
                raise Exception(f"Failed to inspect container {name}: {stderr}")
                
            try:
                return json.loads(stdout)[0]
            except (json.JSONDecodeError, IndexError) as e:
                raise Exception(f"Failed to parse container info: {str(e)}")

    def is_container_running(self, container_name: str = None, callback=None, error_callback=None) -> None:
        """Check if a container is running.
        
        Args:
            container_name: Name of container to check. If None, uses self.container_name
            callback: Function to call with running status (boolean)
            error_callback: Function to call on error
            
        Returns:
            bool: True if container is running (only if no callbacks provided)
        """
        name = container_name or self.container_name
        
        # If callbacks provided, run asynchronously
        if callback:
            def on_inspect_success(container_info):
                running = container_info.get('State', {}).get('Running', False)
                # Call success callback with running status
                self._invoke_callback(callback, running)
            
            # Call inspect with callbacks
            self.inspect_container(name, on_inspect_success, error_callback)
        else:
            # Run synchronously for backwards compatibility
            try:
                info = self.inspect_container(name)
                return info.get('State', {}).get('Running', False)
            except Exception:
                return False

    def list_containers(self, all_containers=True, callback=None, error_callback=None) -> None:
        """List all edge node containers.
        
        Args:
            all_containers: If True, show all containers including stopped ones
            callback: Function to call with results
            error_callback: Function to call on error
        """
        # If callbacks provided, run asynchronously
        if callback:
            thread = QThread()
            
            def run_list():
                try:
                    command = [
                        'docker', 'ps',
                        '--format', '{{.Names}}\t{{.Status}}\t{{.ID}}',
                        '-f', 'name=r1node'
                    ]
                    if all_containers:
                        command.append('-a')
                        
                    stdout, stderr, return_code = self.execute_command(command)
                    if return_code != 0:
                        raise Exception(f"Failed to list containers: {stderr}")
                        
                    containers = []
                    for line in stdout.splitlines():
                        if line.strip():
                            name, status, container_id = line.split('\t')
                            containers.append({
                                'name': name,
                                'status': status,
                                'id': container_id,
                                'running': 'Up' in status
                            })
                    
                    # Call success callback with results
                    self._invoke_callback(callback, containers)
                except Exception as e:
                    logging.error(f"Error listing containers: {str(e)}")
                    if error_callback:
                        self._invoke_callback(error_callback, str(e))
            
            # Connect thread
            thread.run = run_list
            thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
            self.threads.append(thread)
            thread.start()
        else:
            # Run synchronously for backwards compatibility
            command = [
                'docker', 'ps',
                '--format', '{{.Names}}\t{{.Status}}\t{{.ID}}',
                '-f', 'name=r1node'
            ]
            if all_containers:
                command.append('-a')
                
            stdout, stderr, return_code = self.execute_command(command)
            if return_code != 0:
                raise Exception(f"Failed to list containers: {stderr}")
                
            containers = []
            for line in stdout.splitlines():
                if line.strip():
                    name, status, container_id = line.split('\t')
                    containers.append({
                        'name': name,
                        'status': status,
                        'id': container_id,
                        'running': 'Up' in status
                    })
            return containers

    def create_loading_callbacks(self, loading_start_fn, loading_end_fn, on_success_fn=None, on_error_fn=None):
        """Creates a pair of callbacks that handle showing/hiding loading indicators along with success/error actions.
        
        Args:
            loading_start_fn: Function to call to show loading indicator
            loading_end_fn: Function to call to hide loading indicator
            on_success_fn: Optional function to call on successful operation (after loading ends)
            on_error_fn: Optional function to call on operation error (after loading ends)
            
        Returns:
            tuple: (success_callback, error_callback) functions to use with Docker operations
        """
        # Call the loading start function immediately
        if loading_start_fn:
            loading_start_fn()
        
        def success_callback(*args, **kwargs):
            # First hide the loading indicator
            if loading_end_fn:
                loading_end_fn()
            # Then call the success function if provided
            if on_success_fn:
                on_success_fn(*args, **kwargs)
        
        def error_callback(error_message):
            # First hide the loading indicator
            if loading_end_fn:
                loading_end_fn()
            # Then call the error function if provided
            if on_error_fn:
                on_error_fn(error_message)
            else:
                # Default error handling
                logging.error(f"Operation failed: {error_message}")
        
        return success_callback, error_callback

    # Helper method for consistent invocation of Qt callbacks
    def _invoke_callback(self, callback_fn, *args):
        """Helper method to consistently invoke Qt callbacks
        
        Args:
            callback_fn: The callback function to invoke
            *args: Arguments to pass to the callback
        """
        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG, QVariant
        
        # For single arg, use the simpler form
        if len(args) == 0:
            QMetaObject.invokeMethod(callback_fn, Qt.QueuedConnection)
        elif len(args) == 1 and isinstance(callback_fn, str) and callback_fn == "call":
            # This case means we're calling a method named "call" on an object
            # The first arg is the one we're passing to that method
            QMetaObject.invokeMethod(args[0], "call", Qt.QueuedConnection)
        else:
            # Convert all arguments to QVariant for safety
            qt_args = [Q_ARG(QVariant, arg) for arg in args]
            QMetaObject.invokeMethod(callback_fn, "call", Qt.QueuedConnection, *qt_args)

    def start_container_with_loading(self, loading_start_fn, loading_end_fn, volume_name=None, on_success=None, on_error=None):
        """Start a container with loading indicator handling.
        
        Args:
            loading_start_fn: Function to call to show loading indicator
            loading_end_fn: Function to call to hide loading indicator
            volume_name: Optional volume name to mount
            on_success: Optional function to call when container starts successfully
            on_error: Optional function to call if container start fails
        """
        success_cb, error_cb = self.create_loading_callbacks(
            loading_start_fn, loading_end_fn, on_success, on_error
        )
        self.launch_container(volume_name, success_cb, error_cb)
    
    def stop_container_with_loading(self, loading_start_fn, loading_end_fn, container_name=None, on_success=None, on_error=None):
        """Stop a container with loading indicator handling.
        
        Args:
            loading_start_fn: Function to call to show loading indicator
            loading_end_fn: Function to call to hide loading indicator
            container_name: Name of container to stop. If None, uses self.container_name
            on_success: Optional function to call when container stops successfully
            on_error: Optional function to call if container stop fails
        """
        success_cb, error_cb = self.create_loading_callbacks(
            loading_start_fn, loading_end_fn, on_success, on_error
        )
        self.stop_container(container_name, success_cb, error_cb)
