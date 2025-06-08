# Data Models

All refactor-mcp operations use strongly-typed Pydantic models for parameters and responses.

## Core Parameter Types

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple

class Position(BaseModel):
    line: int = Field(ge=1, description="Line number (1-based)")
    column: int = Field(ge=0, description="Column number (0-based)")

class Range(BaseModel):
    start: Position
    end: Position

class AnalyzeParams(BaseModel):
    symbol_name: str = Field(description="Symbol to analyze (qualified name preferred)")

class RenameParams(BaseModel):
    symbol_name: str = Field(description="Current symbol name (qualified name preferred)")
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="New symbol name")

class ExtractParams(BaseModel):
    source: str = Field(description="Function or element to extract from")
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="Name for extracted element")

class FindParams(BaseModel):
    pattern: str = Field(description="Symbol pattern to search for (supports wildcards)")

class ShowParams(BaseModel):
    function_name: str = Field(description="Function to analyze for extractable elements")
```

## Response Models

### Symbol Information

```python
class SymbolInfo(BaseModel):
    name: str
    qualified_name: str = Field(description="Fully qualified symbol name")
    type: str = Field(description="Symbol type (function, class, variable, etc.)")
    definition_location: str = Field(description="File and line where defined")
    scope: str = Field(description="Symbol scope (local, global, class, etc.)")
    docstring: Optional[str] = None

class ElementInfo(BaseModel):
    id: str = Field(description="Auto-generated element ID")
    type: str = Field(description="Element type (lambda, expression, block)")
    code: str = Field(description="Element source code")
    location: str = Field(description="File and line location")
    extractable: bool = Field(description="Whether element can be extracted")
```

### Operation Results

```python
class ShowResult(BaseModel):
    success: bool
    function_name: str
    extractable_elements: List[ElementInfo] = Field(default_factory=list)

class FindResult(BaseModel):
    success: bool
    pattern: str
    matches: List[SymbolInfo] = Field(default_factory=list)
    total_count: int = Field(default=0)

class RenameResult(BaseModel):
    success: bool
    old_name: str
    new_name: str
    qualified_name: str = Field(description="Fully qualified symbol that was renamed")
    files_modified: List[str] = Field(default_factory=list)
    references_updated: int = Field(default=0)
    conflicts: List[str] = Field(default_factory=list)
    backup_id: Optional[str] = None

class ExtractResult(BaseModel):
    success: bool
    source: str = Field(description="What was extracted from")
    new_function_name: str
    extracted_code: str
    parameters: List[str] = Field(default_factory=list)
    return_type: Optional[str] = None
    files_modified: List[str] = Field(default_factory=list)
    backup_id: Optional[str] = None

class AnalysisResult(BaseModel):
    success: bool
    symbol_info: Optional[SymbolInfo] = None
    references: List[str] = Field(default_factory=list, description="List of files containing references")
    reference_count: int = Field(default=0)
    refactoring_suggestions: List[str] = Field(default_factory=list)

class BackupResult(BaseModel):
    success: bool
    backup_id: str
    files_backed_up: List[str] = Field(default_factory=list)
    timestamp: str

class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error_type: str
    message: str
    suggestions: List[str] = Field(default_factory=list)
```

## Validation Patterns

### Symbol Name Validation

```python
SYMBOL_NAME_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'

def validate_symbol_name(name: str) -> bool:
    """Validate that a symbol name follows Python naming conventions"""
    import re
    return bool(re.match(SYMBOL_NAME_PATTERN, name))
```

### Error Response Patterns

```python
def create_error_response(error_type: str, message: str, suggestions: List[str] = None) -> ErrorResponse:
    """Create standardized error response"""
    return ErrorResponse(
        error_type=error_type,
        message=message,
        suggestions=suggestions or []
    )

# Common error types
ERROR_SYMBOL_NOT_FOUND = "symbol_not_found"
ERROR_AMBIGUOUS_SYMBOL = "ambiguous_symbol"
ERROR_INVALID_OPERATION = "invalid_operation"
ERROR_PROVIDER_NOT_FOUND = "provider_not_found"
ERROR_VALIDATION_FAILED = "validation_failed"
```