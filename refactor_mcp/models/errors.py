"""Error models and validation utilities."""

import re
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(default=False)
    error_type: str
    message: str
    suggestions: List[str] = Field(default_factory=list)
    details: Optional[Dict[str, Any]] = None


# Common error types
ERROR_SYMBOL_NOT_FOUND = "symbol_not_found"
ERROR_AMBIGUOUS_SYMBOL = "ambiguous_symbol"
ERROR_INVALID_OPERATION = "invalid_operation"
ERROR_PROVIDER_NOT_FOUND = "provider_not_found"
ERROR_VALIDATION_FAILED = "validation_failed"
ERROR_OPERATION_FAILED = "operation_failed"
ERROR_BACKUP_FAILED = "backup_failed"
ERROR_RESTORE_FAILED = "restore_failed"
ERROR_CONFLICT_DETECTED = "conflict_detected"
ERROR_UNSUPPORTED_LANGUAGE = "unsupported_language"

# Symbol name validation pattern
SYMBOL_NAME_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'


class RefactoringError(Exception):
    """Base exception for refactoring operations."""
    
    def __init__(
        self, 
        error_type: str, 
        message: str, 
        suggestions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.error_type = error_type
        self.message = message
        self.suggestions = suggestions or []
        self.details = details or {}
        self.original_error = original_error
        super().__init__(message)
    
    def to_response(self) -> ErrorResponse:
        """Convert to ErrorResponse model."""
        return ErrorResponse(
            error_type=self.error_type,
            message=self.message,
            suggestions=self.suggestions,
            details=self.details
        )


class SymbolNotFoundError(RefactoringError):
    """Raised when a requested symbol cannot be found."""
    
    def __init__(self, symbol: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            error_type=ERROR_SYMBOL_NOT_FOUND,
            message=f"Symbol '{symbol}' not found",
            suggestions=suggestions or [
                "Check symbol name spelling",
                "Use 'find_symbols' to discover available symbols",
                "Ensure the symbol is in the correct file/module"
            ],
            details={"symbol": symbol}
        )


class AmbiguousSymbolError(RefactoringError):
    """Raised when multiple symbols match a given name."""
    
    def __init__(self, symbol: str, candidates: List[str]):
        super().__init__(
            error_type=ERROR_AMBIGUOUS_SYMBOL,
            message=f"Multiple '{symbol}' symbols found",
            suggestions=[
                f"Use qualified names: {', '.join(candidates)}",
                "Run 'find_symbols' to see all matches"
            ],
            details={"symbol": symbol, "candidates": candidates}
        )


class ConflictDetectedError(RefactoringError):
    """Raised when a refactoring operation would cause conflicts."""
    
    def __init__(self, operation: str, conflicts: List[str]):
        super().__init__(
            error_type=ERROR_CONFLICT_DETECTED,
            message=f"Conflicts detected for {operation}",
            suggestions=[
                "Choose a different name to avoid conflicts",
                "Resolve existing conflicts before proceeding"
            ],
            details={"operation": operation, "conflicts": conflicts}
        )


class UnsupportedLanguageError(RefactoringError):
    """Raised when no provider supports the detected language."""
    
    def __init__(self, language: str, file_path: Optional[str] = None):
        super().__init__(
            error_type=ERROR_UNSUPPORTED_LANGUAGE,
            message=f"No provider available for language: {language}",
            suggestions=[
                "Check if the file extension is supported",
                "Consider using a different provider",
                "File an issue to request language support"
            ],
            details={"language": language, "file_path": file_path}
        )


class ValidationError(RefactoringError):
    """Raised when operation parameters fail validation."""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            error_type=ERROR_VALIDATION_FAILED,
            message=f"Validation failed for {field}: {reason}",
            suggestions=["Check parameter format and constraints"],
            details={"field": field, "value": str(value), "reason": reason}
        )


class ProviderError(RefactoringError):
    """Raised when a provider operation fails."""
    
    def __init__(self, provider: str, operation: str, original_error: Exception):
        super().__init__(
            error_type=ERROR_OPERATION_FAILED,
            message=f"Provider {provider} failed during {operation}: {str(original_error)}",
            suggestions=[
                "Check file permissions and syntax",
                "Ensure all dependencies are available",
                "Try a different approach or provider"
            ],
            details={"provider": provider, "operation": operation},
            original_error=original_error
        )


class BackupError(RefactoringError):
    """Raised when backup operations fail."""
    
    def __init__(self, operation: str, reason: str):
        super().__init__(
            error_type=ERROR_BACKUP_FAILED,
            message=f"Backup failed for {operation}: {reason}",
            suggestions=[
                "Check disk space and permissions",
                "Ensure backup directory is accessible",
                "Consider manual backup before proceeding"
            ],
            details={"operation": operation, "reason": reason}
        )


def validate_symbol_name(name: str) -> bool:
    """Validate that a symbol name follows Python naming conventions."""
    return bool(re.match(SYMBOL_NAME_PATTERN, name))


def create_error_response(
    error_type: str, 
    message: str, 
    suggestions: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """Create standardized error response."""
    return ErrorResponse(
        error_type=error_type,
        message=message,
        suggestions=suggestions or [],
        details=details
    )