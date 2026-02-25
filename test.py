import time
from tinyoscquery.query import OSCQueryBrowser, OSCQueryClient
from pythonosc import udp_client

def try_connect(tries: int = 5, delay: float = 1):# -> Any | None:
    """Try to connect to VRChat OSCQuery service with retries"""
    browser = OSCQueryBrowser()
    
    for _ in range(tries):
        vrchat_service = browser.find_service_by_name("VRChat")
        if vrchat_service:
            print("VRChat service found!")
            return vrchat_service
        time.sleep(delay)
    
    print("Failed to find VRChat service after multiple attempts.")
    return None

def get_parameter(client, parameter_path):
    """
    Get a specific parameter by its path.
    
    Args:
        client: OSCQueryClient instance
        parameter_path: String path to the parameter (e.g., "/avatar/parameters/VRCEmote")
    
    Returns:
        OSCQueryNode if found, None otherwise
    """
    try:
        node = client.query_node(parameter_path)
        if node is None:
            print(f"Parameter '{parameter_path}' not found.")
            return None
        return node
    except Exception as e:
        print(f"Error querying parameter '{parameter_path}': {e}")
        return None

def set_parameter(client, host_info, parameter_path, value):
    """
    Set a parameter to a specific value with type validation.
    
    Args:
        client: OSCQueryClient instance
        host_info: OSCHostInfo with connection details
        parameter_path: String path to the parameter
        value: Value to set
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # First, query the parameter to get its type
        node = get_parameter(client, parameter_path)
        if node is None:
            return False
        
        # Check if parameter is writable
        if node.access is not None and node.access.value in [0, 1]:  # NO_VALUE or READONLY_VALUE
            print(f"Error: Parameter '{parameter_path}' is read-only (Access: {node.access.name})")
            return False
        
        # Validate type if available
        if node.type_ is not None and len(node.type_) > 0:
            expected_type = node.type_[0]
            
            # Type validation
            if expected_type == bool:
                if not isinstance(value, bool):
                    if isinstance(value, (int, str)):
                        # Try to convert
                        if isinstance(value, str):
                            if value.lower() in ['true', '1', 'yes']:
                                value = True
                            elif value.lower() in ['false', '0', 'no']:
                                value = False
                            else:
                                print(f"Error: Cannot convert '{value}' to bool")
                                return False
                        else:
                            value = bool(value)
                    else:
                        print(f"Error: Expected bool, got {type(value).__name__}")
                        return False
                        
            elif expected_type == int:
                if not isinstance(value, int):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        print(f"Error: Cannot convert '{value}' to int")
                        return False
                        
            elif expected_type == float:
                if not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        print(f"Error: Cannot convert '{value}' to float")
                        return False
                        
            elif expected_type == str:
                value = str(value)
        
        # Create OSC client and send the message
        osc_client = udp_client.SimpleUDPClient(host_info.osc_ip, host_info.osc_port)
        osc_client.send_message(parameter_path, value)
        
        # successfully sent the message
        return True
        
    except Exception as e:
        print(f"Error setting parameter '{parameter_path}': {e}")
        return False


def main():
    print("Searching for VRChat OSCQuery service...")
    browser = OSCQueryBrowser()
    vrchat_service = try_connect()
    
    if vrchat_service is None:
        return
    # Create client for VRChat service
    client = OSCQueryClient(vrchat_service)
    
    # Get host info
    host_info = client.get_host_info()
    print(f"\nConnected to: {host_info.name}")
    print(f"OSC IP: {host_info.osc_ip}")
    print(f"OSC Port: {host_info.osc_port}")
    print(f"Transport: {host_info.osc_transport}")
    
    avatar_parameters_node = client.query_node("/avatar/parameters")
    if avatar_parameters_node is None:
        print("Failed to query avatar parameters.")
        return

    # Try to get a common VRChat parameter
    param = get_parameter(client, "/avatar/parameters/VRCEmote")
    if param:
        print(f"Found parameter: {param.full_path}")
        print(f"  Type: {param.type_}")
        print(f"  Value: {param.value}")
        print(f"  Access: {param.access.name if param.access else 'Unknown'}")
    
    # To set a parameter, uncomment the following line:"
    set_parameter(client, host_info, '/avatar/parameters/VRCEmote', 20)

    time.sleep(1)

    set_parameter(client, host_info, '/avatar/parameters/VRCEmote', 0)

    time.sleep(1)

    set_parameter(client, host_info, '/avatar/parameters/MuteSelf', 1)

    time.sleep(1)

    set_parameter(client, host_info, '/avatar/parameters/MuteSelf', 0)



if __name__ == "__main__":
    main()
