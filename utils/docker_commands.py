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

    def _ensure_image_exists(self) -> bool:
        """Check if the Docker image exists locally and pull it if not.
        
        Returns:
            bool: True if image exists or was pulled successfully, False otherwise
        """
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

    def check_and_pull_image_updates(self, image_name: str = None, tag: str = None) -> tuple:
        """Check if a Docker image has updates available and pull if it does.
        
        Args:
            image_name: Docker image name (defaults to DOCKER_IMAGE)
            tag: Docker image tag (defaults to DOCKER_TAG)
            
        Returns:
            tuple: (was_updated, message)
                was_updated: True if the image was updated, False otherwise
                message: Informational message about what happened
        """
        # Use default if not specified
        image_name = image_name or DOCKER_IMAGE
        tag = tag or DOCKER_TAG
        
        full_image_name = f"{image_name}:{tag}"
        
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

    def launch_container(self, volume_name: str = None) -> None:
        """Launch the container with an optional volume.
        
        Args:
            volume_name: Optional volume name to mount
        """
        # Ensure image exists
        self._ensure_image_exists()
        
        # Check if a container with the same name already exists
        inspect_command = ['docker', 'container', 'inspect', self.container_name]
        stdout, stderr, return_code = self.execute_command(inspect_command)
        
        # If container exists (return code 0), remove it
        if return_code == 0:
            remove_command = ['docker', 'rm', '-f', self.container_name]
            stdout, stderr, return_code = self.execute_command(remove_command)
            if return_code != 0:
                raise Exception(f"Failed to remove existing container: {stderr}")
        
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

    def list_containers(self, all_containers=True) -> list:
        """List all edge node containers.
        
        Args:
            all_containers: If True, show all containers including stopped ones
            
        Returns:
            list: List of container dictionaries with info
        """
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

    def stop_container(self, container_name: str = None) -> None:
        """Stop a container.
        
        Args:
            container_name: Name of container to stop. If None, uses self.container_name
        """
        name = container_name or self.container_name
        command = ['docker', 'stop', name]
        stdout, stderr, return_code = self.execute_command(command)
        if return_code != 0:
            raise Exception(f"Failed to stop container {name}: {stderr}")

    def remove_container(self, container_name: str = None, force: bool = False) -> None:
        """Remove a container.
        
        Args:
            container_name: Name of container to remove. If None, uses self.container_name
            force: If True, force remove even if running
        """
        name = container_name or self.container_name
        command = ['docker', 'rm']
        if force:
            command.append('-f')
        command.append(name)
        
        stdout, stderr, return_code = self.execute_command(command)
        if return_code != 0:
            raise Exception(f"Failed to remove container {name}: {stderr}")

        # Remove from registry
        self.registry.remove_container(name)

    def inspect_container(self, container_name: str = None) -> dict:
        """Get detailed information about a container.
        
        Args:
            container_name: Name of container to inspect. If None, uses self.container_name
            
        Returns:
            dict: Container information
        """
        name = container_name or self.container_name
        command = ['docker', 'inspect', name]
        stdout, stderr, return_code = self.execute_command(command)
        if return_code != 0:
            raise Exception(f"Failed to inspect container {name}: {stderr}")
            
        try:
            return json.loads(stdout)[0]
        except (json.JSONDecodeError, IndexError) as e:
            raise Exception(f"Failed to parse container info: {str(e)}")

    def is_container_running(self, container_name: str = None) -> bool:
        """Check if a container is running.
        
        Args:
            container_name: Name of container to check. If None, uses self.container_name
            
        Returns:
            bool: True if container is running
        """
        try:
            info = self.inspect_container(container_name)
            return info.get('State', {}).get('Running', False)
        except Exception:
            return False
