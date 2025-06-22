"""
System Resources Mixin

This module provides functionality for monitoring system resources like memory, CPU, and storage.
It follows the same pattern as other mixins in the codebase (_DockerUtilsMixin, _UpdaterMixin).
"""

import os
import platform
import shutil
import multiprocessing

# Try to import psutil, fall back to system commands if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class _SystemResourcesMixin:
    """Mixin class for system resource monitoring functionality."""

    def __init__(self):
        super().__init__()
        self._last_resources_check = 0
        self._cached_resources = None
        self._cache_duration = 5  # Cache resources for 5 seconds to avoid excessive system calls

    def get_system_resources(self, use_cache=True):
        """Get system resource information (memory, CPU, storage).
        
        Args:
            use_cache (bool): Whether to use cached results if available
            
        Returns:
            dict: Dictionary containing memory, cpu, and storage information
        """
        from time import time
        
        # Use cached data if available and not expired
        if (use_cache and self._cached_resources and 
            (time() - self._last_resources_check) < self._cache_duration):
            return self._cached_resources
        
        resources = {
            'memory': {'available': 'N/A', 'total': 'N/A', 'percent': 'N/A'},
            'cpu': {'count': 'N/A', 'usage': 'N/A'},
            'storage': {'free': 'N/A', 'total': 'N/A', 'percent': 'N/A'}
        }
        
        try:
            if PSUTIL_AVAILABLE:
                # Get memory information
                memory = psutil.virtual_memory()
                resources['memory']['available'] = memory.available
                resources['memory']['total'] = memory.total
                resources['memory']['percent'] = memory.percent
                
                # Get CPU information
                resources['cpu']['count'] = psutil.cpu_count(logical=True)
                # Get CPU usage (1 second interval for accuracy)
                resources['cpu']['usage'] = psutil.cpu_percent(interval=0.1)
                
                # Get storage information for current directory
                disk = psutil.disk_usage('/')  # Unix/Linux
                if platform.system() == 'Windows':
                    disk = psutil.disk_usage('C:\\')
                resources['storage']['free'] = disk.free
                resources['storage']['total'] = disk.total
                resources['storage']['percent'] = (disk.used / disk.total) * 100
            else:
                # Fallback methods when psutil is not available
                
                # CPU count fallback
                try:
                    resources['cpu']['count'] = multiprocessing.cpu_count()
                    # CPU usage fallback (not available without psutil)
                    resources['cpu']['usage'] = 'N/A'
                except:
                    resources['cpu']['count'] = 'N/A'
                    resources['cpu']['usage'] = 'N/A'
                
                # Memory fallback (Linux/Mac)
                if platform.system() in ['Linux', 'Darwin']:
                    try:
                        # Try to read /proc/meminfo on Linux
                        if platform.system() == 'Linux' and os.path.exists('/proc/meminfo'):
                            with open('/proc/meminfo', 'r') as f:
                                meminfo = f.read()
                            lines = meminfo.split('\n')
                            for line in lines:
                                if 'MemTotal:' in line:
                                    total_kb = int(line.split()[1])
                                    resources['memory']['total'] = total_kb * 1024
                                elif 'MemAvailable:' in line:
                                    available_kb = int(line.split()[1])
                                    resources['memory']['available'] = available_kb * 1024
                            
                            if (resources['memory']['total'] != 'N/A' and 
                                resources['memory']['available'] != 'N/A'):
                                used = resources['memory']['total'] - resources['memory']['available']
                                resources['memory']['percent'] = (used / resources['memory']['total']) * 100
                    except:
                        pass
                
                # Storage fallback using shutil
                try:
                    if platform.system() == 'Windows':
                        path = 'C:\\'
                    else:
                        path = '/'
                    total, used, free = shutil.disk_usage(path)
                    resources['storage']['free'] = free
                    resources['storage']['total'] = total
                    resources['storage']['percent'] = (used / total) * 100
                except:
                    pass
                    
        except Exception as e:
            # If any error occurs, log it if we have add_log method
            if hasattr(self, 'add_log'):
                self.add_log(f"Error getting system resources: {str(e)}", debug=True)
        
        # Cache the results
        if use_cache:
            self._cached_resources = resources
            self._last_resources_check = time()
        
        return resources

    def format_bytes(self, bytes_value):
        """Format bytes to human readable format.
        
        Args:
            bytes_value: Number of bytes or 'N/A'
            
        Returns:
            str: Formatted string like '8.2 GB' or 'N/A'
        """
        if bytes_value == 'N/A' or bytes_value is None:
            return 'N/A'
        
        try:
            bytes_value = float(bytes_value)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        except:
            return 'N/A'

    def get_formatted_memory_info(self):
        """Get formatted memory information.
        
        Returns:
            str: Formatted memory string like "8.2 GB / 16.0 GB (51.2% used)"
        """
        resources = self.get_system_resources()
        
        if (resources['memory']['available'] != 'N/A' and 
            resources['memory']['total'] != 'N/A'):
            available_str = self.format_bytes(resources['memory']['available'])
            total_str = self.format_bytes(resources['memory']['total'])
            percent = resources['memory']['percent']
            if percent != 'N/A':
                return f"{available_str} / {total_str} ({percent:.1f}% used)"
            else:
                return f"{available_str} / {total_str}"
        else:
            return 'N/A'

    def get_formatted_cpu_info(self):
        """Get formatted CPU information.
        
        Returns:
            str: Formatted CPU string like "8 cores (15.2% used)"
        """
        resources = self.get_system_resources()
        
        count = resources['cpu']['count']
        usage = resources['cpu']['usage']
        
        if count != 'N/A' and usage != 'N/A':
            return f"{count} cores ({usage:.1f}% used)"
        elif count != 'N/A':
            return f"{count} cores"
        elif usage != 'N/A':
            return f"{usage:.1f}% used"
        else:
            return 'N/A'

    def get_formatted_storage_info(self):
        """Get formatted storage information.
        
        Returns:
            str: Formatted storage string like "189.8 GB / 273.9 GB (25.6% used)"
        """
        resources = self.get_system_resources()
        
        if (resources['storage']['free'] != 'N/A' and 
            resources['storage']['total'] != 'N/A'):
            free_str = self.format_bytes(resources['storage']['free'])
            total_str = self.format_bytes(resources['storage']['total'])
            percent = resources['storage']['percent']
            if percent != 'N/A':
                return f"{free_str} / {total_str} ({percent:.1f}% used)"
            else:
                return f"{free_str} / {total_str}"
        else:
            return 'N/A'

    def clear_resources_cache(self):
        """Clear the cached resources data to force fresh data on next call."""
        self._cached_resources = None
        self._last_resources_check = 0

    def get_available_ram_bytes(self):
        """Get available RAM in bytes.
        
        Returns:
            int or str: Available RAM in bytes, or 'N/A' if not available
        """
        resources = self.get_system_resources()
        return resources['memory']['available']

    def get_total_ram_bytes(self):
        """Get total RAM in bytes.
        
        Returns:
            int or str: Total RAM in bytes, or 'N/A' if not available
        """
        resources = self.get_system_resources()
        return resources['memory']['total']

    def bytes_to_gb(self, bytes_value):
        """Convert bytes to GB.
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            float: Value in GB
        """
        if bytes_value == 'N/A' or bytes_value is None:
            return 'N/A'
        try:
            return float(bytes_value) / (1024 ** 3)
        except:
            return 'N/A'

    def gb_to_bytes(self, gb_value):
        """Convert GB to bytes.
        
        Args:
            gb_value: Value in GB
            
        Returns:
            int: Value in bytes
        """
        try:
            return int(float(gb_value) * (1024 ** 3))
        except:
            return 0

    def calculate_available_ram_for_nodes(self, existing_node_count=0):
        """Calculate maximum nodes based on total RAM capacity.
        
        Args:
            existing_node_count (int): Number of existing nodes
            
        Returns:
            dict: Dictionary with node capacity information
        """
        from utils.const import MIN_NODE_RAM_GB
        
        total_ram_bytes = self.get_total_ram_bytes()
        
        if total_ram_bytes == 'N/A':
            return {
                'can_add_node': False,
                'error': 'Unable to determine system RAM'
            }
        
        total_ram_gb = self.bytes_to_gb(total_ram_bytes)
        used_by_nodes_gb = existing_node_count * MIN_NODE_RAM_GB
        
        # Calculate maximum nodes system can support based on total RAM
        # Simple formula: total RAM / RAM per node
        max_nodes_supported = int(total_ram_gb // MIN_NODE_RAM_GB)
        
        # Check if we can add another node
        can_add_node = existing_node_count < max_nodes_supported
        
        return {
            'total_ram_gb': total_ram_gb,
            'used_by_nodes_gb': used_by_nodes_gb,
            'max_nodes_supported': max_nodes_supported,
            'current_node_count': existing_node_count,
            'can_add_node': can_add_node,
            'min_required_gb': MIN_NODE_RAM_GB
        }

    def check_ram_for_new_node(self, existing_node_count=0):
        """Check if there's enough RAM to add a new node.
        
        Args:
            existing_node_count (int): Number of existing nodes
            
        Returns:
            dict: Dictionary with check results and details
        """
        ram_info = self.calculate_available_ram_for_nodes(existing_node_count)
        
        if 'error' in ram_info:
            return ram_info
        
        can_add = ram_info['can_add_node']
        
        # Return all the detailed information from ram_info plus the message
        result = ram_info.copy()
        result['message'] = self._get_ram_check_message(ram_info, can_add)
        result['required_gb'] = ram_info['min_required_gb']  # Add this for backward compatibility
        
        return result

    def _get_ram_check_message(self, ram_info, can_add):
        """Generate a user-friendly message about RAM capacity.
        
        Args:
            ram_info (dict): RAM information
            can_add (bool): Whether a new node can be added
            
        Returns:
            str: User-friendly message
        """
        if can_add:
            return (f"Node can be created. System supports {ram_info['max_nodes_supported']} nodes total "
                   f"({ram_info['total_ram_gb']:.1f} GB ÷ {ram_info['min_required_gb']} GB per node), "
                   f"currently running {ram_info['current_node_count']} nodes")
        else:
            return (f"Maximum node capacity reached. System supports {ram_info['max_nodes_supported']} nodes "
                   f"({ram_info['total_ram_gb']:.1f} GB ÷ {ram_info['min_required_gb']} GB per node), "
                   f"currently running {ram_info['current_node_count']} nodes") 