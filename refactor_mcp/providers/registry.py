"""Provider registry and routing"""

from typing import List, Dict, Optional
from pathlib import Path
from .base import RefactoringProvider


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
            for provider in self.providers:
                if provider.supports_language(language):
                    self._language_cache[language] = provider
                    break
            else:
                self._language_cache[language] = None

        return self._language_cache[language]

    def get_supported_languages(self) -> List[str]:
        """Get list of all supported languages"""
        languages = set()
        for provider in self.providers:
            # This would need to be implemented by providers
            # For now, we'll assume Python support
            if hasattr(provider, "_supported_languages"):
                languages.update(provider._supported_languages)
        return list(languages)


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    suffix = Path(file_path).suffix.lower()
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".rs": "rust",
        ".ex": "elixir",
        ".go": "go",
    }
    return language_map.get(suffix, "unknown")


def find_project_root(start_path: str) -> str:
    """Find project root by looking for markers."""
    current = Path(start_path).absolute()
    markers = [".git", "pyproject.toml", "setup.py", "Cargo.toml", "package.json"]

    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return str(current)
        current = current.parent

    return str(Path(start_path).absolute())


# Global engine instance
engine = RefactoringEngine()
