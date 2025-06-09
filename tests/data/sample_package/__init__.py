"""
Sample package for testing package-level refactoring operations.

This package demonstrates:
- Package imports and exports
- Cross-module dependencies
- Module structure for refactoring testing
"""

from .core import DataManager, ProcessingEngine
from .utils import helper_function, format_data
from .exceptions import ValidationError, ProcessingError

__version__ = "1.0.0"
__all__ = [
    "DataManager",
    "ProcessingEngine", 
    "helper_function",
    "format_data",
    "ValidationError",
    "ProcessingError"
]