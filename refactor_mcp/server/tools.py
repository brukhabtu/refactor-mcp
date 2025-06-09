"""MCP tool definitions for refactor-mcp operations."""

from pydantic import Field, ValidationError
from typing import Union

from . import app, detect_language_from_symbol, detect_project_language, handle_operation_error
from ..models.params import AnalyzeParams, FindParams, ShowParams, RenameParams, ExtractParams
from ..models.responses import (
    AnalysisResult, FindResult, ShowResult, RenameResult, ExtractResult
)
from ..models.errors import ErrorResponse


@app.tool()
def refactor_analyze_symbol(
    symbol_name: str = Field(description="Symbol to analyze (use qualified names for disambiguation)")
) -> Union[AnalysisResult, ErrorResponse]:
    """Analyze symbol for refactoring opportunities and get reference information."""
    try:
        language = detect_language_from_symbol(symbol_name)
        provider = app._refactoring_engine.get_provider(language)

        if not provider:
            return ErrorResponse(
                error_type="provider_not_found",
                message=f"No refactoring support for {language}",
                suggestions=["Currently only Python is supported via Rope provider"]
            )

        params = AnalyzeParams(symbol_name=symbol_name)
        return provider.analyze_symbol(params)

    except ValidationError as e:
        return ErrorResponse(
            error_type="validation_error",
            message=str(e),
            suggestions=["Check symbol name format, use qualified names like 'module.function'"]
        )
    except Exception as e:
        return handle_operation_error("Symbol analysis", e)


@app.tool()
def refactor_find_symbols(
    pattern: str = Field(description="Symbol pattern to search for (supports wildcards)")
) -> Union[FindResult, ErrorResponse]:
    """Find symbols matching a pattern across the project."""
    try:
        # Auto-detect project language from files
        language = detect_project_language()
        provider = app._refactoring_engine.get_provider(language)

        if not provider:
            return ErrorResponse(
                error_type="provider_not_found",
                message=f"No refactoring support for detected language: {language}"
            )

        params = FindParams(pattern=pattern)
        return provider.find_symbols(params)

    except Exception as e:
        return ErrorResponse(
            error_type="search_error",
            message=str(e),
            suggestions=["Check pattern syntax, use wildcards like '*.method' or 'module.*'"]
        )


@app.tool()
def refactor_show_function(
    function_name: str = Field(description="Function to analyze for extractable elements")
) -> Union[ShowResult, ErrorResponse]:
    """Show extractable elements (lambdas, expressions, blocks) within a function."""
    try:
        language = detect_language_from_symbol(function_name)
        provider = app._refactoring_engine.get_provider(language)

        if not provider:
            return ErrorResponse(
                error_type="provider_not_found",
                message=f"No refactoring support for {language}"
            )

        params = ShowParams(function_name=function_name)
        return provider.show_function(params)

    except Exception as e:
        return ErrorResponse(
            error_type="analysis_error",
            message=str(e),
            suggestions=["Ensure function exists and use qualified names like 'module.function'"]
        )


@app.tool()
def refactor_rename_symbol(
    symbol_name: str = Field(description="Current symbol name (qualified name preferred)"),
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="New symbol name")
) -> Union[RenameResult, ErrorResponse]:
    """Safely rename symbol across scope with conflict detection."""
    try:
        language = detect_language_from_symbol(symbol_name)
        provider = app._refactoring_engine.get_provider(language)

        if not provider:
            return ErrorResponse(
                error_type="provider_not_found",
                message=f"No refactoring support for {language}"
            )

        params = RenameParams(symbol_name=symbol_name, new_name=new_name)
        return provider.rename_symbol(params)

    except ValidationError as e:
        return ErrorResponse(
            error_type="validation_error",
            message=str(e),
            suggestions=["New name must be valid Python identifier (letters, numbers, underscores)"]
        )
    except Exception as e:
        return handle_operation_error("Symbol rename", e)


@app.tool()
def refactor_extract_element(
    source: str = Field(description="Source function or element ID to extract from"),
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="Name for extracted element")
) -> Union[ExtractResult, ErrorResponse]:
    """Extract code element (function, lambda, expression, or block) into new function."""
    try:
        language = detect_language_from_symbol(source)
        provider = app._refactoring_engine.get_provider(language)

        if not provider:
            return ErrorResponse(
                error_type="provider_not_found",
                message=f"No refactoring support for {language}"
            )

        params = ExtractParams(source=source, new_name=new_name)
        return provider.extract_element(params)

    except ValidationError as e:
        return ErrorResponse(
            error_type="validation_error",
            message=str(e),
            suggestions=["Check source format, use 'function.lambda_1' for anonymous elements"]
        )
    except Exception as e:
        return handle_operation_error("Element extraction", e)