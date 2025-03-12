"""Docker utility functions."""

def get_volume_name(container_name):
    """Get volume name from container name.
    
    Args:
        container_name: Name of the container
        
    Returns:
        str: Name of the volume
    """
    # For legacy container names
    if "edge_node_container" in container_name:
        return container_name.replace("container", "volume")
    
    # For new r1node naming convention
    if container_name == "r1node":
        return "r1vol"  # First container gets simple volume name
    
    # For r1node with sequential numbers
    if container_name.startswith("r1node"):
        # Extract the number part
        try:
            # Get the numeric part after "r1node"
            number_part = container_name[6:]
            if number_part.isdigit():
                return f"r1vol{number_part}"
        except (ValueError, IndexError):
            pass
    
    # Fallback
    return f"volume_{container_name}"

def generate_container_name(prefix="r1node"):
    """Generate a sequential container name.
    
    First container is named just "r1node" (no number),
    subsequent containers are "r1node1", "r1node2", etc.
    
    Args:
        prefix: Prefix for the container name
        
    Returns:
        str: Sequential container name
    """
    import subprocess
    
    # Get list of existing containers with the prefix
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}', '--filter', f'name={prefix}'],
            capture_output=True, text=True
        )
        
        # Parse existing container names and find the highest index
        existing_containers = result.stdout.strip().split('\n')
        existing_containers = [c for c in existing_containers if c]  # Remove empty strings
        
        highest_index = -1  # Start from -1 so first container will be r1node0
        for container in existing_containers:
            if container.startswith(prefix):
                try:
                    # Extract the number after the prefix
                    index_str = container[len(prefix):]
                    if index_str.isdigit():
                        index = int(index_str)
                        highest_index = max(highest_index, index)
                except (ValueError, IndexError):
                    continue
        
        # Return next available index
        return f"{prefix}{highest_index + 1}"
        
    except Exception as e:
        # In case of any error, start from 0
        return f"{prefix}0" 