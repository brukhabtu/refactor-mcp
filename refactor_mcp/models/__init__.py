"""Data models for refactor-mcp operations.

This module provides Pydantic models for all MCP operations including
parameter validation, response serialization, and error handling.
"""

from .params import (
    Position,
    Range,
    AnalyzeParams,
    RenameParams,
    ExtractParams,
    FindParams,
    ShowParams,
)

from .responses import (
    SymbolInfo,
    ElementInfo,
    ShowResult,
    FindResult,
    RenameResult,
    ExtractResult,
    AnalysisResult,
    BackupResult,
)

from .errors import (
    ErrorResponse,
    create_error_response,
    ERROR_SYMBOL_NOT_FOUND,
    ERROR_AMBIGUOUS_SYMBOL,
    ERROR_INVALID_OPERATION,
    ERROR_PROVIDER_NOT_FOUND,
    ERROR_VALIDATION_FAILED,
    validate_symbol_name,
    SYMBOL_NAME_PATTERN,
)

__all__ = [
    # Parameter models
    "Position",
    "Range",
    "AnalyzeParams",
    "RenameParams",
    "ExtractParams",
    "FindParams",
    "ShowParams",
    # Response models
    "SymbolInfo",
    "ElementInfo",
    "ShowResult",
    "FindResult",
    "RenameResult",
    "ExtractResult",
    "AnalysisResult",
    "BackupResult",
    # Error handling
    "ErrorResponse",
    "create_error_response",
    "ERROR_SYMBOL_NOT_FOUND",
    "ERROR_AMBIGUOUS_SYMBOL",
    "ERROR_INVALID_OPERATION",
    "ERROR_PROVIDER_NOT_FOUND",
    "ERROR_VALIDATION_FAILED",
    "validate_symbol_name",
    "SYMBOL_NAME_PATTERN",
]
