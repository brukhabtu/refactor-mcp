from typing import Protocol, List, Optional, Dict
from pathlib import Path

from ..models import (
    AnalyzeParams, AnalysisResult,
    RenameParams, RenameResult,
    ExtractParams, ExtractResult,
    FindParams, FindResult,
    ShowParams, ShowResult
)


class RefactoringProvider(Protocol):
    """Standard interface for all refactoring engines"""

    def supports_language(self, language: str) -> bool:
        """Check if this provider handles the given language"""
        ...

    def get_capabilities(self, language: str) -> List[str]:
        """Return list of supported operations for language"""
        ...

    def rename_symbol(self, params: RenameParams) -> RenameResult:
        """Safely rename symbol across scope"""
        ...

    def find_symbols(self, params: FindParams) -> FindResult:
        """Find symbols matching a pattern"""
        ...

    def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
        """Get symbol information and refactoring opportunities"""
        ...

    def show_function(self, params: ShowParams) -> ShowResult:
        """Show extractable elements within a function"""
        ...

    def extract_element(self, params: ExtractParams) -> ExtractResult:
        """Extract code element (function, lambda, expression, or block)"""
        ...


class RefactoringEngine:
    """Central registry and router for refactoring providers"""

    def __init__(self):
        self.providers: List[RefactoringProvider] = []
        self._language_cache: Dict[str, Optional[RefactoringProvider]] = {}

    def register_provider(self, provider: RefactoringProvider):
        """Register a new refactoring provider"""
        self.providers.append(provider)
        self._language_cache.clear()

    def get_provider(self, language: str) -> Optional[RefactoringProvider]:
        """Get best provider for language (cached)"""
        if language not in self._language_cache:
            found_provider = None
            for provider in self.providers:
                if provider.supports_language(language):
                    found_provider = provider
                    break
            self._language_cache[language] = found_provider

        return self._language_cache[language]


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    suffix = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.rs': 'rust',
        '.ex': 'elixir',
        '.go': 'go'
    }
    return language_map.get(suffix, 'unknown')


def find_project_root(start_path: str) -> str:
    """Find project root by looking for markers"""
    current = Path(start_path).absolute()
    markers = ['.git', 'pyproject.toml', 'setup.py', 'Cargo.toml', 'package.json']

    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return str(current)
        current = current.parent

    return str(Path(start_path).absolute())


# Global engine instance
engine = RefactoringEngine()