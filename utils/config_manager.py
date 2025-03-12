import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from utils.const import CONFIG_DIR

# Container configuration structure
class ContainerConfig:
    def __init__(self, name: str, volume: str, created_at: str = None, last_used: str = None, 
                 node_address: str = None, eth_address: str = None, node_alias: str = None):
        self.name = name
        self.volume = volume
        self.created_at = created_at
        self.last_used = last_used
        self.node_address = node_address
        self.eth_address = eth_address
        self.node_alias = node_alias
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "volume": self.volume,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "node_address": self.node_address,
            "eth_address": self.eth_address,
            "node_alias": self.node_alias
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContainerConfig':
        return cls(
            name=data.get("name", ""),
            volume=data.get("volume", ""),
            created_at=data.get("created_at"),
            last_used=data.get("last_used"),
            node_address=data.get("node_address"),
            eth_address=data.get("eth_address"),
            node_alias=data.get("node_alias")
        )


class ConfigManager:
    """Manages container configurations stored in a local config file."""
    
    def __init__(self, config_dir: str = None):
        """Initialize the config manager.
        
        Args:
            config_dir: Directory to store config files. Defaults to ~/.ratio1/edge_node_launcher/
        """
        if config_dir is None:
            home_dir = str(Path.home())
            self.config_dir = os.path.join(home_dir, CONFIG_DIR)
        else:
            self.config_dir = config_dir
            
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.containers_file = os.path.join(self.config_dir, "containers.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        self.containers: List[ContainerConfig] = []
        self.settings = {}
        
        # Load existing configurations
        self.load_containers()
        self.load_settings()
    
    def load_containers(self) -> List[ContainerConfig]:
        """Load container configurations from file."""
        try:
            if os.path.exists(self.containers_file):
                with open(self.containers_file, 'r') as f:
                    data = json.load(f)
                    self.containers = [ContainerConfig.from_dict(item) for item in data]
            return self.containers
        except Exception as e:
            logging.error(f"Error loading container configurations: {str(e)}")
            return []
    
    def save_containers(self) -> bool:
        """Save container configurations to file."""
        try:
            with open(self.containers_file, 'w') as f:
                json.dump([container.to_dict() for container in self.containers], f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving container configurations: {str(e)}")
            return False
    
    def add_container(self, container: ContainerConfig) -> bool:
        """Add a new container configuration."""
        # Check if container already exists
        for existing in self.containers:
            if existing.name == container.name:
                # Update existing container
                existing.volume = container.volume
                existing.created_at = container.created_at
                existing.last_used = container.last_used
                # Preserve addresses if they exist and new ones are not provided
                if container.node_address:
                    existing.node_address = container.node_address
                if container.eth_address:
                    existing.eth_address = container.eth_address
                return self.save_containers()
        
        # Add new container
        self.containers.append(container)
        return self.save_containers()
    
    def remove_container(self, container_name: str) -> bool:
        """Remove a container configuration."""
        self.containers = [c for c in self.containers if c.name != container_name]
        return self.save_containers()
    
    def get_container(self, container_name: str) -> Optional[ContainerConfig]:
        """Get a container configuration by name."""
        for container in self.containers:
            if container.name == container_name:
                return container
        return None
    
    def get_all_containers(self) -> List[ContainerConfig]:
        """Get all container configurations."""
        return self.containers
    
    def update_last_used(self, container_name: str, timestamp: str) -> bool:
        """Update the last used timestamp for a container."""
        container = self.get_container(container_name)
        if container:
            container.last_used = timestamp
            return self.save_containers()
        return False
    
    def update_node_address(self, container_name: str, node_address: str) -> bool:
        """Update the node address for a container.
        
        Args:
            container_name: Name of the container
            node_address: Node address to save
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        container = self.get_container(container_name)
        if container:
            container.node_address = node_address
            return self.save_containers()
        return False
    
    def update_eth_address(self, container_name: str, eth_address: str) -> bool:
        """Update the ETH address for a container.
        
        Args:
            container_name: Name of the container
            eth_address: New ETH address
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            container = self.get_container(container_name)
            if container:
                container.eth_address = eth_address
                self.save_containers()
                return True
            return False
        except Exception as e:
            logging.error(f"Error updating ETH address: {str(e)}")
            return False
    
    def update_node_alias(self, container_name: str, node_alias: str) -> bool:
        """Update the node alias for a container.
        
        Args:
            container_name: Name of the container
            node_alias: New node alias
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            container = self.get_container(container_name)
            if container:
                container.node_alias = node_alias
                self.save_containers()
                return True
            return False
        except Exception as e:
            logging.error(f"Error updating node alias: {str(e)}")
            return False
    
    def update_volume(self, container_name: str, volume_name: str) -> bool:
        """Update the volume name for a container.
        
        Args:
            container_name: Name of the container
            volume_name: Volume name to save
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        container = self.get_container(container_name)
        if container:
            container.volume = volume_name
            return self.save_containers()
        return False
    
    def volume_exists_in_docker(self, volume_name: str) -> bool:
        """Check if a volume exists in Docker.
        
        Args:
            volume_name: Name of the volume to check
            
        Returns:
            bool: True if the volume exists, False otherwise
        """
        try:
            import subprocess
            import os
            
            # Command to check if volume exists
            command = ['docker', 'volume', 'inspect', volume_name]
            
            # Execute command
            if os.name == 'nt':
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(command, capture_output=True, text=True)
                
            # Return True if command was successful (volume exists)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Error checking if volume exists: {str(e)}")
            return False
    
    def export_containers(self, export_file: str) -> bool:
        """Export container configurations to a file.
        
        Args:
            export_file: Path to the export file
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            with open(export_file, 'w') as f:
                json.dump([container.to_dict() for container in self.containers], f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error exporting container configurations: {str(e)}")
            return False
    
    def import_containers(self, import_file: str) -> bool:
        """Import container configurations from a file.
        
        Args:
            import_file: Path to the import file
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        try:
            if os.path.exists(import_file):
                with open(import_file, 'r') as f:
                    data = json.load(f)
                    imported_containers = [ContainerConfig.from_dict(item) for item in data]
                    
                    # Merge with existing containers
                    for imported in imported_containers:
                        self.add_container(imported)
                    
                    return True
            return False
        except Exception as e:
            logging.error(f"Error importing container configurations: {str(e)}")
            return False
    
    def load_settings(self) -> dict:
        """Load settings from file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            return self.settings
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
            return {}
    
    def save_settings(self) -> bool:
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving settings: {str(e)}")
            return False
    
    def set_force_debug(self, enabled: bool) -> bool:
        """Set force debug mode.
        
        Args:
            enabled: Whether to enable force debug mode
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.settings['force_debug'] = enabled
            return self.save_settings()
        except Exception as e:
            logging.error(f"Error setting force debug mode: {str(e)}")
            return False
    
    def get_force_debug(self) -> bool:
        """Get force debug mode setting.
        
        Returns:
            bool: True if force debug is enabled, False otherwise
        """
        return self.settings.get('force_debug', False) 