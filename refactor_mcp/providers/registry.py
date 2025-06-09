"""Provider registry and routing"""

from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
import threading
import logging
from .base import RefactoringProvider

logger = logging.getLogger(__name__)


@dataclass
class ProviderInfo:
    """Information about a registered provider"""
    provider: RefactoringProvider
    priority: int = 1
    capabilities_cache: Dict[str, List[str]] = field(default_factory=dict)
    last_health_check: Optional[float] = None
    is_loaded: bool = False


class RefactoringEngine:
    """Enhanced central registry and router for refactoring providers"""

    def __init__(self):
        self._providers: List[ProviderInfo] = []
        self._language_cache: Dict[str, List[RefactoringProvider]] = {}
        self._best_provider_cache: Dict[str, Optional[RefactoringProvider]] = {}
        self._capability_cache: Dict[tuple, List[str]] = {}
        self._lock = threading.RLock()

    def register_provider(self, provider: RefactoringProvider, priority: int = 1):
        """Register a new refactoring provider with priority"""
        with self._lock:
            provider_info = ProviderInfo(provider=provider, priority=priority)
            self._providers.append(provider_info)
            self._clear_caches()
            logger.info(f"Registered provider {getattr(provider, 'name', 'unknown')} with priority {priority}")

    def get_provider(self, language: str) -> Optional[RefactoringProvider]:
        """Get best provider for language (backward compatibility)"""
        return self.get_best_provider(language)

    def get_providers(self, language: str) -> List[RefactoringProvider]:
        """Get all providers that support the given language, sorted by priority"""
        with self._lock:
            if language not in self._language_cache:
                providers = []
                for provider_info in self._providers:
                    if provider_info.provider.supports_language(language):
                        providers.append(provider_info)
                
                # Sort by priority (highest first)
                providers.sort(key=lambda x: x.priority, reverse=True)
                self._language_cache[language] = [p.provider for p in providers]
            
            return self._language_cache[language].copy()

    def get_best_provider(self, language: str) -> Optional[RefactoringProvider]:
        """Get highest priority provider for language"""
        with self._lock:
            if language not in self._best_provider_cache:
                providers = self.get_providers(language)
                self._best_provider_cache[language] = providers[0] if providers else None
            
            return self._best_provider_cache[language]

    def get_providers_with_capability(self, language: str, capability: str) -> List[RefactoringProvider]:
        """Get providers that support specific capability for language"""
        providers = []
        for provider in self.get_providers(language):
            capabilities = self.get_cached_capabilities(language, provider)
            if capability in capabilities:
                providers.append(provider)
        return providers

    def get_cached_capabilities(self, language: str, provider: RefactoringProvider) -> List[str]:
        """Get cached capabilities for provider and language"""
        cache_key = (id(provider), language)
        
        if cache_key not in self._capability_cache:
            capabilities = provider.get_capabilities(language)
            self._capability_cache[cache_key] = capabilities
        
        return self._capability_cache[cache_key]

    def get_healthy_providers(self, language: str) -> List[RefactoringProvider]:
        """Get providers that pass health checks"""
        healthy = []
        for provider in self.get_providers(language):
            if self._is_provider_healthy(provider):
                healthy.append(provider)
        return healthy

    def execute_with_fallback(self, operation: str, language: str, *args, **kwargs) -> Any:
        """Execute operation with automatic fallback to next provider on failure"""
        providers = self.get_providers(language)  # Try all providers, not just healthy ones
        
        if not providers:
            raise RuntimeError(f"No providers available for language: {language}")
        
        last_exception = None
        healthy_providers_tried = []
        
        for provider in providers:
            try:
                operation_method = getattr(provider, operation)
                result = operation_method(*args, **kwargs)
                logger.debug(f"Operation {operation} succeeded with provider {getattr(provider, 'name', 'unknown')}")
                return result
            except Exception as e:
                last_exception = e
                logger.warning(f"Provider {getattr(provider, 'name', 'unknown')} failed for {operation}: {e}")
                if self._is_provider_healthy(provider):
                    healthy_providers_tried.append(provider)
                continue
        
        if not healthy_providers_tried:
            raise RuntimeError(f"No healthy providers available for language: {language}")
        else:
            raise RuntimeError(f"All providers failed for {operation}") from last_exception

    def execute_operation(self, operation: str, language: str, *args, **kwargs) -> Any:
        """Execute operation using best available provider"""
        provider = self.get_best_provider(language)
        if not provider:
            raise RuntimeError(f"No provider available for language: {language}")
        
        operation_method = getattr(provider, operation)
        return operation_method(*args, **kwargs)

    def discover_and_register_providers(self, discovered_providers: List[RefactoringProvider]):
        """Auto-register discovered providers"""
        for provider in discovered_providers:
            priority = getattr(provider, 'priority', 1)
            self.register_provider(provider, priority)

    def load_provider(self, provider: RefactoringProvider):
        """Load a provider (lifecycle management)"""
        with self._lock:
            provider_info = self._find_provider_info(provider)
            if provider_info and hasattr(provider, 'load'):
                provider.load()
                provider_info.is_loaded = True
                logger.info(f"Loaded provider {getattr(provider, 'name', 'unknown')}")

    def unload_provider(self, provider: RefactoringProvider):
        """Unload and remove a provider (lifecycle management)"""
        with self._lock:
            provider_info = self._find_provider_info(provider)
            if provider_info:
                if hasattr(provider, 'unload'):
                    provider.unload()
                self._providers.remove(provider_info)
                self._clear_caches()
                logger.info(f"Unloaded provider {getattr(provider, 'name', 'unknown')}")

    def get_supported_languages(self) -> List[str]:
        """Get list of all supported languages"""
        languages = set()
        for provider_info in self._providers:
            provider = provider_info.provider
            if hasattr(provider, '_supported_languages'):
                languages.update(provider._supported_languages)
            else:
                # Fallback: try to detect supported languages
                for lang in ['python', 'javascript', 'typescript', 'rust', 'go']:
                    if provider.supports_language(lang):
                        languages.add(lang)
        return list(languages)

    def _find_provider_info(self, provider: RefactoringProvider) -> Optional[ProviderInfo]:
        """Find provider info for given provider"""
        for provider_info in self._providers:
            if provider_info.provider == provider:
                return provider_info
        return None

    def _is_provider_healthy(self, provider: RefactoringProvider) -> bool:
        """Check if provider is healthy"""
        if hasattr(provider, 'is_healthy'):
            return provider.is_healthy()
        return True  # Assume healthy if no health check method

    def _clear_caches(self):
        """Clear all caches"""
        self._language_cache.clear()
        self._best_provider_cache.clear()
        self._capability_cache.clear()


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
