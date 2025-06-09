"""
Utility functions for the sample package.

Contains helper functions that reference core module functions,
demonstrating cross-module dependencies for refactoring testing.
"""

import json
import re
from typing import Any, List, Dict, Union


def helper_function(data: Any) -> str:
    """
    Helper function that processes various data types.
    
    This function is referenced by core.py and demonstrates
    cross-module refactoring scenarios.
    """
    if data is None:
        return "null"
    
    # Type-specific processing for extraction testing
    if isinstance(data, (int, float)):
        return f"number:{data}"
    elif isinstance(data, str):
        return f"string:{data}"
    elif isinstance(data, (list, tuple)):
        return f"list:{len(data)}"
    elif isinstance(data, dict):
        return f"dict:{len(data)}"
    else:
        return f"object:{type(data).__name__}"


def format_data(data: Any, format_type: str = "json") -> str:
    """
    Format data according to specified type.
    
    Function that could be renamed and used across modules.
    """
    # Format mapping for extraction testing
    formatters = {
        "json": lambda d: json.dumps(d, default=str, indent=2),
        "repr": lambda d: repr(d),
        "str": lambda d: str(d),
        "summary": lambda d: f"Type: {type(d).__name__}, Value: {str(d)[:50]}"
    }
    
    if format_type not in formatters:
        raise ValueError(f"Unsupported format: {format_type}")
    
    try:
        return formatters[format_type](data)
    except Exception as e:
        return f"Format error: {e}"


def validate_input(value: Any) -> bool:
    """
    Validate input value.
    
    Referenced by core.py for data validation.
    """
    # Basic validation rules for extraction testing
    validation_rules = [
        lambda v: v is not None,  # Not None
        lambda v: not (isinstance(v, str) and len(v) == 0),  # Not empty string
        lambda v: not (isinstance(v, (list, dict)) and len(v) == 0),  # Not empty container
    ]
    
    # Apply all validation rules
    return all(rule(value) for rule in validation_rules)


def sanitize_string(text: str) -> str:
    """
    Sanitize string input for safe processing.
    
    Contains extractable regex patterns and logic.
    """
    if not isinstance(text, str):
        return str(text)
    
    # Sanitization steps for extraction testing
    def remove_html_tags(input_text):
        """Remove HTML tags from text."""
        html_pattern = re.compile(r'<[^>]+>')
        return html_pattern.sub('', input_text)
    
    def normalize_whitespace(input_text):
        """Normalize whitespace in text."""
        # Multiple whitespace normalization patterns
        space_pattern = re.compile(r'\s+')
        normalized = space_pattern.sub(' ', input_text)
        return normalized.strip()
    
    def escape_special_chars(input_text):
        """Escape special characters."""
        # Character escaping for extraction testing
        escape_map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, escape in escape_map.items():
            input_text = input_text.replace(char, escape)
        
        return input_text
    
    # Apply sanitization pipeline
    cleaned = remove_html_tags(text)
    cleaned = normalize_whitespace(cleaned)
    cleaned = escape_special_chars(cleaned)
    
    return cleaned


def batch_process(items: List[Any], processor_func, batch_size: int = 10) -> List[Any]:
    """
    Process items in batches.
    
    Demonstrates batch processing patterns for refactoring.
    """
    if not items:
        return []
    
    results = []
    
    # Batch processing logic for extraction testing
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Process batch with error handling
        batch_results = []
        for item in batch:
            try:
                processed = processor_func(item)
                batch_results.append(processed)
            except Exception as e:
                # Error handling for extraction testing
                error_result = {
                    "error": str(e),
                    "original_item": item,
                    "position": len(results) + len(batch_results)
                }
                batch_results.append(error_result)
        
        results.extend(batch_results)
    
    return results


def data_converter(data: Any, target_type: str) -> Any:
    """
    Convert data to target type.
    
    Contains type conversion logic for extraction testing.
    """
    # Conversion functions for extraction testing
    converters = {
        "string": lambda x: str(x),
        "int": lambda x: int(float(x)) if isinstance(x, str) else int(x),
        "float": lambda x: float(x),
        "bool": lambda x: bool(x) if not isinstance(x, str) else x.lower() in ('true', '1', 'yes'),
        "list": lambda x: list(x) if hasattr(x, '__iter__') and not isinstance(x, str) else [x],
        "dict": lambda x: dict(x) if hasattr(x, 'items') else {"value": x}
    }
    
    if target_type not in converters:
        available = ", ".join(converters.keys())
        raise ValueError(f"Unsupported target type: {target_type}. Available: {available}")
    
    try:
        return converters[target_type](data)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Cannot convert {type(data).__name__} to {target_type}: {e}")


def merge_dictionaries(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries with conflict resolution.
    
    Demonstrates complex merging logic for extraction testing.
    """
    if not dicts:
        return {}
    
    result = {}
    
    # Conflict resolution strategies for extraction testing
    def resolve_conflict(key, existing_value, new_value):
        """Resolve conflicts when merging dictionaries."""
        # Strategy: newer values win, but merge nested dicts
        if isinstance(existing_value, dict) and isinstance(new_value, dict):
            return merge_dictionaries(existing_value, new_value)
        else:
            return new_value
    
    # Merge all dictionaries
    for dictionary in dicts:
        if not isinstance(dictionary, dict):
            continue
        
        for key, value in dictionary.items():
            if key in result:
                result[key] = resolve_conflict(key, result[key], value)
            else:
                result[key] = value
    
    return result


def calculate_statistics(numbers: List[Union[int, float]]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of numbers.
    
    Contains mathematical calculations for extraction testing.
    """
    if not numbers:
        return {}
    
    # Filter valid numbers
    valid_numbers = [n for n in numbers if isinstance(n, (int, float)) and not (isinstance(n, float) and (n != n))]  # Filter NaN
    
    if not valid_numbers:
        return {}
    
    # Statistical calculations for extraction testing
    def calculate_mean(values):
        """Calculate arithmetic mean."""
        return sum(values) / len(values)
    
    def calculate_variance(values, mean_value):
        """Calculate variance."""
        squared_diffs = [(x - mean_value) ** 2 for x in values]
        return sum(squared_diffs) / len(values)
    
    def calculate_std_dev(variance_value):
        """Calculate standard deviation."""
        import math
        return math.sqrt(variance_value)
    
    # Calculate all statistics
    mean = calculate_mean(valid_numbers)
    variance = calculate_variance(valid_numbers, mean)
    std_dev = calculate_std_dev(variance)
    
    return {
        "count": len(valid_numbers),
        "sum": sum(valid_numbers),
        "mean": mean,
        "variance": variance,
        "std_dev": std_dev,
        "min": min(valid_numbers),
        "max": max(valid_numbers),
        "range": max(valid_numbers) - min(valid_numbers)
    }