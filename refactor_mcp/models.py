from pydantic import BaseModel, Field
from typing import List, Optional


class AnalyzeParams(BaseModel):
    symbol_name: str = Field(description="Symbol to analyze (qualified name preferred)")


class RenameParams(BaseModel):
    symbol_name: str = Field(
        description="Current symbol name (qualified name preferred)"
    )
    new_name: str = Field(
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$", description="New symbol name"
    )


class ExtractParams(BaseModel):
    source: str = Field(description="Function or element to extract from")
    new_name: str = Field(
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$", description="Name for extracted element"
    )


class FindParams(BaseModel):
    pattern: str = Field(
        description="Symbol pattern to search for (supports wildcards)"
    )


class ShowParams(BaseModel):
    function_name: str = Field(
        description="Function to analyze for extractable elements"
    )


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


class ShowResult(BaseModel):
    success: bool
    function_name: str = ""
    extractable_elements: List[ElementInfo] = Field(default_factory=list)
    error_type: Optional[str] = None
    message: Optional[str] = None


class FindResult(BaseModel):
    success: bool
    pattern: str = ""
    matches: List[SymbolInfo] = Field(default_factory=list)
    total_count: int = Field(default=0)
    error_type: Optional[str] = None
    message: Optional[str] = None


class RenameResult(BaseModel):
    success: bool
    old_name: str = ""
    new_name: str = ""
    qualified_name: str = Field(
        default="", description="Fully qualified symbol that was renamed"
    )
    files_modified: List[str] = Field(default_factory=list)
    references_updated: int = Field(default=0)
    conflicts: List[str] = Field(default_factory=list)
    backup_id: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None


class ExtractResult(BaseModel):
    success: bool
    source: str = Field(default="", description="What was extracted from")
    new_function_name: str = ""
    extracted_code: str = ""
    parameters: List[str] = Field(default_factory=list)
    return_type: Optional[str] = None
    files_modified: List[str] = Field(default_factory=list)
    backup_id: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None


class AnalysisResult(BaseModel):
    success: bool
    symbol_info: Optional[SymbolInfo] = None
    references: List[str] = Field(
        default_factory=list, description="List of files containing references"
    )
    reference_count: int = Field(default=0)
    refactoring_suggestions: List[str] = Field(default_factory=list)
    error_type: Optional[str] = None
    message: Optional[str] = None
