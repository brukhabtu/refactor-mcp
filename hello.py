def hello_world() -> str:
    """Return a simple hello world message.
    
    Returns:
        str: The hello world greeting message.
    """
    return "Hello, World!"


def greet(name: str) -> str:
    """Return a personalized greeting message.
    
    Args:
        name: The name of the person to greet.
        
    Returns:
        str: A personalized greeting message.
    """
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(hello_world())
    print(greet("Claude"))