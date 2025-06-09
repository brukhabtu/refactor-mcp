"""MCP server implementation for refactor-mcp.

This module provides the FastMCP server setup and configuration
for AI-optimized refactoring operations.
"""

import os
import time
from typing import Optional

import fastmcp

from ..providers.registry import RefactoringEngine
from ..models.errors import ErrorResponse, create_error_response


def detect_language_from_symbol(symbol_name: str) -> str:
    """Detect language from symbol name patterns.
    
    Currently defaults to Python as the only supported language.
    Future versions will support multi-language detection.
    """
    return "python"


def detect_project_language() -> str:
    """Detect primary language of the current project.
    
    Scans common file extensions and patterns to determine
    the primary programming language.
    """
    return "python"


def handle_operation_error(operation: str, error: Exception, context: Optional[str] = None) -> ErrorResponse:
    """Standardized error handling for MCP operations."""
    
    error_mappings = {
        "SymbolNotFoundError": ("symbol_not_found", ["Use 'refactor_find_symbols' to discover available symbols"]),
        "AmbiguousSymbolError": ("ambiguous_symbol", ["Use qualified names like 'module.Class.method'"]),
        "UnsupportedLanguageError": ("provider_not_found", ["Currently only Python is supported"]),
        "ValidationError": ("validation_error", ["Check parameter format and requirements"])
    }
    
    error_type = type(error).__name__
    error_info = error_mappings.get(error_type, ("internal_error", []))
    
    message = f"{operation} failed: {str(error)}"
    if context:
        message += f" (Context: {context})"
    
    return create_error_response(
        error_type=error_info[0],
        message=message,
        suggestions=error_info[1]
    )


def create_mcp_server() -> fastmcp.FastMCP:
    """Create and configure the MCP server."""
    
    mcp = fastmcp.FastMCP("refactor-mcp")
    
    # Initialize the refactoring engine
    engine = RefactoringEngine()
    
    # Register providers
    try:
        from ..providers.rope_provider import RopeProvider
        engine.register_provider(RopeProvider())
    except ImportError:
        pass  # Rope provider not yet implemented
    
    # Add development middleware for debugging
    if os.getenv("REFACTOR_MCP_DEBUG"):
        @mcp.middleware()
        def debug_middleware(request, call_next):
            start = time.time()
            response = call_next(request)
            duration = time.time() - start
            print(f"MCP tool call: {request.tool_name} took {duration:.2f}s")
            return response
    
    # Store engine instance for tool access
    mcp._refactoring_engine = engine
    
    return mcp


# Export the configured server
app = create_mcp_server()