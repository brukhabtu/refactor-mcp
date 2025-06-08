# MCP Server Interface

The MCP server provides AI-optimized tool interfaces for programmatic consumption by Claude Code and other MCP-compatible systems.

## FastMCP Server Setup

```python
import fastmcp
from pydantic import ValidationError, Field

mcp = fastmcp.FastMCP("refactor-mcp")
```

## Core MCP Tools

### Symbol Analysis

```python
@mcp.tool()
def refactor_analyze_symbol(
    symbol_name: str = Field(description="Symbol to analyze (use qualified names for disambiguation)")
) -> AnalysisResult:
    """Analyze symbol for refactoring opportunities and get reference information"""
    try:
        language = detect_language_from_symbol(symbol_name)
        provider = engine.get_provider(language)

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
        return ErrorResponse(
            error_type="internal_error",
            message=str(e)
        )
```

### Symbol Discovery

```python
@mcp.tool()
def refactor_find_symbols(
    pattern: str = Field(description="Symbol pattern to search for (supports wildcards)")
) -> FindResult:
    """Find symbols matching a pattern across the project"""
    try:
        # Auto-detect project language from files
        language = detect_project_language()
        provider = engine.get_provider(language)

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
```

### Function Element Discovery

```python
@mcp.tool()
def refactor_show_function(
    function_name: str = Field(description="Function to analyze for extractable elements")
) -> ShowResult:
    """Show extractable elements (lambdas, expressions, blocks) within a function"""
    try:
        language = detect_language_from_symbol(function_name)
        provider = engine.get_provider(language)

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
```

### Symbol Renaming

```python
@mcp.tool()
def refactor_rename_symbol(
    symbol_name: str = Field(description="Current symbol name (qualified name preferred)"),
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="New symbol name")
) -> RenameResult:
    """Safely rename symbol across scope with conflict detection"""
    try:
        language = detect_language_from_symbol(symbol_name)
        provider = engine.get_provider(language)

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
        return ErrorResponse(
            error_type="rename_error",
            message=str(e)
        )
```

### Element Extraction

```python
@mcp.tool()
def refactor_extract_element(
    source: str = Field(description="Source function or element ID to extract from"),
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="Name for extracted element")
) -> ExtractResult:
    """Extract code element (function, lambda, expression, or block) into new function"""
    try:
        language = detect_language_from_symbol(source)
        provider = engine.get_provider(language)

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
        return ErrorResponse(
            error_type="extraction_error",
            message=str(e)
        )
```

## Error Handling Strategy

### Standardized Error Responses

All MCP tools return either success results or standardized error responses:

```python
def handle_operation_error(operation: str, error: Exception, context: str = None) -> ErrorResponse:
    """Standardized error handling for MCP operations"""
    
    error_mappings = {
        "SymbolNotFoundError": ("symbol_not_found", ["Use 'refactor_find_symbols' to discover available symbols"]),
        "AmbiguousSymbolError": ("ambiguous_symbol", ["Use qualified names like 'module.Class.method'"]),
        "UnsupportedLanguageError": ("provider_not_found", ["Currently only Python is supported"]),
        "ValidationError": ("validation_error", ["Check parameter format and requirements"])
    }
    
    error_type = type(error).__name__
    error_info = error_mappings.get(error_type, ("internal_error", []))
    
    return ErrorResponse(
        error_type=error_info[0],
        message=f"{operation} failed: {str(error)}",
        suggestions=error_info[1]
    )
```

### Language Detection

Language detection utilities are defined in **[Architecture](architecture.md)** to avoid duplication.

## Server Configuration

```python
def create_mcp_server():
    """Create and configure the MCP server"""
    
    # Register providers
    from .providers.rope_provider import RopeProvider
    engine.register_provider(RopeProvider())
    
    # Add development middleware for debugging
    if os.getenv("REFACTOR_MCP_DEBUG"):
        @mcp.middleware()
        def debug_middleware(request, call_next):
            import time
            start = time.time()
            response = call_next(request)
            duration = time.time() - start
            print(f"MCP tool call: {request.tool_name} took {duration:.2f}s")
            return response
    
    return mcp

# Export the configured server
app = create_mcp_server()
```