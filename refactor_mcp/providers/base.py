"""Base provider protocol and utilities"""

from typing import Protocol, List, Dict, Any, Optional
from pydantic import BaseModel
from ..models.params import (
    AnalyzeParams,
    RenameParams,
    ExtractParams,
    FindParams,
    ShowParams,
)
from ..models.responses import (
    AnalysisResult,
    RenameResult,
    ExtractResult,
    FindResult,
    ShowResult,
)


class ProviderMetadata(BaseModel):
    """Metadata information about a refactoring provider"""

    name: str
    version: str
    description: str
    author: str
    supported_languages: List[str]
    min_protocol_version: str = "1.0.0"
    max_protocol_version: str = "1.0.0"


class OperationCapability(BaseModel):
    """Information about a specific operation capability"""

    name: str
    support_level: str  # "full", "partial", "experimental"
    description: Optional[str] = None
    limitations: Optional[List[str]] = None


class ProviderHealthStatus(BaseModel):
    """Health status information for a provider"""

    status: str  # "healthy", "degraded", "unhealthy"
    details: Dict[str, Any]
    dependencies: List[str]
    last_check: Optional[str] = None


class RefactoringProvider(Protocol):
    """Standard interface for all refactoring engines"""

    def supports_language(self, language: str) -> bool:
        """Check if this provider handles the given language"""
        ...

    def get_capabilities(self, language: str) -> List[str]:
        """Return list of supported operations for language"""
        ...

    def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
        """Get symbol information and refactoring opportunities"""
        ...

    def find_symbols(self, params: FindParams) -> FindResult:
        """Find symbols matching a pattern"""
        ...

    def show_function(self, params: ShowParams) -> ShowResult:
        """Show extractable elements within a function"""
        ...

    def rename_symbol(self, params: RenameParams) -> RenameResult:
        """Safely rename symbol across scope"""
        ...

    def extract_element(self, params: ExtractParams) -> ExtractResult:
        """Extract code element (function, lambda, expression, or block)"""
        ...

    # Enhanced protocol methods
    def get_metadata(self) -> ProviderMetadata:
        """Get provider metadata including name, version, and capabilities"""
        ...

    def get_detailed_capabilities(
        self, language: str
    ) -> Dict[str, List[OperationCapability]]:
        """Get detailed capability information organized by operation category"""
        ...

    def health_check(self) -> ProviderHealthStatus:
        """Perform health check and return status information"""
        ...

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate provider configuration and return validation results"""
        ...

    def get_priority(self, language: str) -> int:
        """Get provider priority for language-specific operations (higher = better)"""
        ...

    def is_compatible(self, protocol_version: str) -> bool:
        """Check if provider is compatible with given protocol version"""
        ...
