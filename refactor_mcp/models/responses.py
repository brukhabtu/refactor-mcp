"""Response models for MCP operations."""

from pydantic import BaseModel, Field
from typing import List, Optional


class SymbolInfo(BaseModel):
    """Information about a symbol."""
    name: str
    qualified_name: str = Field(description="Fully qualified symbol name")
    type: str = Field(description="Symbol type (function, class, variable, etc.)")
    definition_location: str = Field(description="File and line where defined")
    scope: str = Field(description="Symbol scope (local, global, class, etc.)")
    docstring: Optional[str] = None


class ElementInfo(BaseModel):
    """Information about an extractable element."""
    id: str = Field(description="Auto-generated element ID")
    type: str = Field(description="Element type (lambda, expression, block)")
    code: str = Field(description="Element source code")
    location: str = Field(description="File and line location")
    extractable: bool = Field(description="Whether element can be extracted")


class ShowResult(BaseModel):
    """Result of show operation."""
    success: bool
    function_name: Optional[str] = None
    extractable_elements: List[ElementInfo] = Field(default_factory=list)
    error_type: Optional[str] = None
    message: Optional[str] = None


class FindResult(BaseModel):
    """Result of find operation."""
    success: bool
    pattern: Optional[str] = None
    matches: List[SymbolInfo] = Field(default_factory=list)
    total_count: int = Field(default=0)
    error_type: Optional[str] = None
    message: Optional[str] = None


class RenameResult(BaseModel):
    """Result of rename operation."""
    success: bool
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    qualified_name: Optional[str] = Field(default=None, description="Fully qualified symbol that was renamed")
    files_modified: List[str] = Field(default_factory=list)
    references_updated: int = Field(default=0)
    conflicts: List[str] = Field(default_factory=list)
    backup_id: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None


class ExtractResult(BaseModel):
    """Result of extract operation."""
    success: bool
    source: Optional[str] = Field(default=None, description="What was extracted from")
    new_function_name: Optional[str] = None
    extracted_code: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)
    return_type: Optional[str] = None
    files_modified: List[str] = Field(default_factory=list)
    backup_id: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None


class AnalysisResult(BaseModel):
    """Result of analysis operation."""
    success: bool
    symbol_info: Optional[SymbolInfo] = None
    references: List[str] = Field(default_factory=list, description="List of files containing references")
    reference_count: int = Field(default=0)
    refactoring_suggestions: List[str] = Field(default_factory=list)
    error_type: Optional[str] = None
    message: Optional[str] = None


class BackupResult(BaseModel):
    """Result of backup operation."""
    success: bool
    backup_id: str
    files_backed_up: List[str] = Field(default_factory=list)
    timestamp: str