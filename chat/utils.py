from typing import Any, Dict, List
from colorama import Fore, Style, init

# Initialize colorama
init()

# Keep track of printed messages to prevent duplicates
_printed_messages = set()

def normalize_role(role: str) -> str:
    """Normalize role names to ensure consistent formatting."""
    role_mapping = {
        'AIMessage': 'Ai Message',
        'HumanMessage': 'Human Message',
        'ToolMessage': 'Tool Message',
        'assistant': 'Ai Message',
        'user': 'Human Message',
        'tool': 'Tool Message'
    }
    return role_mapping.get(role, role)

def pretty_print(message: Any) -> None:
    """
    Pretty print a message with proper formatting and colors.
    
    Args:
        message: The message to print. Can be a string, dict, or any object with role and content attributes.
    """
    # Get role and content
    role = getattr(message, 'role', type(message).__name__)
    content = getattr(message, 'content', str(message))
    
    # Normalize role name
    role = normalize_role(role)
    
    # Create a unique identifier for this message
    message_id = f"{role}:{content}"
    
    # Skip if this message has already been printed
    if message_id in _printed_messages:
        return
    
    # Add to printed messages set
    _printed_messages.add(message_id)
    
    # Format role with color and style
    role_color = {
        'Human Message': Fore.BLUE,
        'Ai Message': Fore.GREEN,
        'Tool Message': Fore.MAGENTA,
        'system': Fore.YELLOW
    }.get(role, Fore.WHITE)
    
    # Print header with exact format
    print("\n" + "="*50)
    print(f"{role_color}{Style.BRIGHT}{role}{Style.RESET_ALL}")
    print("="*50)
    
    # Handle different message types
    if role == 'Tool Message':
        # For tool messages, display the tool name and result
        if hasattr(message, 'name'):
            print(f"Name: {message.name}")
        elif hasattr(message, 'tool'):
            print(f"Name: {message.tool}")
        print()  # Add empty line after tool name
        print(content)
    elif role == 'Ai Message':
        # For AI messages, handle tool calls and responses
        if isinstance(content, str):
            if "Tool Calls:" in content:
                # Split content into tool calls and response
                parts = content.split("Tool Calls:")
                if len(parts) > 1:
                    print("Tool Calls:")
                    tool_call_part = parts[1].strip()
                    if "Call ID:" in tool_call_part:
                        tool_parts = tool_call_part.split("Call ID:")
                        tool_name = tool_parts[0].strip()
                        call_id = tool_parts[1].split("\n")[0].strip()
                        args = "\n".join(tool_parts[1].split("\n")[1:]).strip()
                        
                        print(f"  {tool_name} ({call_id})")
                        print(f" Call ID: {call_id}")
                        if args:
                            print(f"  Args:\n{args}")
                    else:
                        print(tool_call_part)
                    
                    if len(parts) > 2:
                        print("\nResponse:")
                        print(parts[2].strip())
                else:
                    print(content)
            else:
                # Only print non-tool-call content
                if not hasattr(message, 'additional_kwargs') or not message.additional_kwargs.get('tool_calls'):
                    print(content)
    else:
        # For other message types, just print the content
        if isinstance(content, (dict, list)):
            import json
            print(json.dumps(content, indent=2, ensure_ascii=False))
        else:
            print(content)

    # Check for additional tool call information in message attributes
    if hasattr(message, 'additional_kwargs'):
        tool_calls = message.additional_kwargs.get('tool_calls', [])
        if tool_calls and role == 'Ai Message':  # Only print tool calls for AI messages
            print("\nTool Calls:")
            for tool_call in tool_calls:
                # Extract tool name from function name
                tool_name = tool_call.get('function', {}).get('name', 'Unknown Tool')
                call_id = tool_call.get('id', 'No ID')
                args = tool_call.get('function', {}).get('arguments', {})
                
                print(f"  {tool_name}")
                print(f" Call ID: {call_id}")
                if args:
                    try:
                        import json
                        args_dict = json.loads(args)
                        print("  Args:")
                        for key, value in args_dict.items():
                            print(f"    {key}: {value}")
                    except:
                        print(f"  Args: {args}") 