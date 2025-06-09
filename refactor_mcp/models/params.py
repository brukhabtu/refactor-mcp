"""Parameter models for MCP operations."""

from pydantic import BaseModel, Field


class Position(BaseModel):
    """Position in a source file."""
    line: int = Field(ge=1, description="Line number (1-based)")
    column: int = Field(ge=0, description="Column number (0-based)")


class Range(BaseModel):
    """Range in a source file."""
    start: Position
    end: Position


class AnalyzeParams(BaseModel):
    """Parameters for symbol analysis operation."""
    symbol_name: str = Field(description="Symbol to analyze (qualified name preferred)")


class RenameParams(BaseModel):
    """Parameters for symbol renaming operation."""
    symbol_name: str = Field(description="Current symbol name (qualified name preferred)")
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="New symbol name")


class ExtractParams(BaseModel):
    """Parameters for extraction operation."""
    source: str = Field(description="Function or element to extract from")
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="Name for extracted element")


class FindParams(BaseModel):
    """Parameters for symbol finding operation."""
    pattern: str = Field(description="Symbol pattern to search for (supports wildcards)")


class ShowParams(BaseModel):
    """Parameters for showing extractable elements."""
    function_name: str = Field(description="Function to analyze for extractable elements")