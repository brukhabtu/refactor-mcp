"""Base provider protocol and utilities"""

from typing import Protocol, List
from ..models.params import AnalyzeParams, RenameParams, ExtractParams, FindParams, ShowParams
from ..models.responses import AnalysisResult, RenameResult, ExtractResult, FindResult, ShowResult


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