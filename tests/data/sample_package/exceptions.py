"""
Custom exceptions for the sample package.

Demonstrates exception hierarchies and error handling
patterns for refactoring testing.
"""


class PackageBaseException(Exception):
    """Base exception for all package-specific exceptions."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary representation."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code
        }


class ValidationError(PackageBaseException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field_name: str = None, invalid_value=None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field_name = field_name
        self.invalid_value = invalid_value
    
    def to_dict(self) -> dict:
        """Convert validation error to dictionary with additional fields."""
        base_dict = super().to_dict()
        base_dict.update({
            "field_name": self.field_name,
            "invalid_value": str(self.invalid_value) if self.invalid_value is not None else None
        })
        return base_dict


class ProcessingError(PackageBaseException):
    """Raised when data processing operations fail."""
    
    def __init__(self, message: str, operation: str = None, original_exception: Exception = None):
        super().__init__(message, "PROCESSING_ERROR")
        self.operation = operation
        self.original_exception = original_exception
    
    def to_dict(self) -> dict:
        """Convert processing error to dictionary with operation details."""
        base_dict = super().to_dict()
        base_dict.update({
            "operation": self.operation,
            "original_error": str(self.original_exception) if self.original_exception else None
        })
        return base_dict


class ConfigurationError(PackageBaseException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: str = None, expected_type: str = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key
        self.expected_type = expected_type


class ResourceError(PackageBaseException):
    """Raised when resource operations fail."""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        super().__init__(message, "RESOURCE_ERROR")
        self.resource_type = resource_type
        self.resource_id = resource_id