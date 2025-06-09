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
    symbol: str = Field(description="Symbol to analyze (qualified name preferred)")
    file_path: str = Field(description="Path to file containing the symbol")


class RenameParams(BaseModel):
    """Parameters for symbol renaming operation."""
    old_name: str = Field(description="Current symbol name (qualified name preferred)")
    new_name: str = Field(pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$', description="New symbol name")
    file_path: str = Field(description="Path to file containing the symbol")


class ExtractParams(BaseModel):
    """Parameters for extraction operation."""
    element_type: str = Field(description="Type of element to extract")
    element_id: str = Field(description="ID of element to extract")
    file_path: str = Field(description="Path to file containing the element")


class FindParams(BaseModel):
    """Parameters for symbol finding operation."""
    pattern: str = Field(description="Symbol pattern to search for (supports wildcards)")
    file_path: str = Field(description="Path to file to search in", default="")


class ShowParams(BaseModel):
    """Parameters for showing extractable elements."""
    function_name: str = Field(description="Function to analyze for extractable elements")
    file_path: str = Field(description="Path to file containing the function")