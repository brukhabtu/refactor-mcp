"""Central refactoring engine with provider registration and operation routing"""

import uuid
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models.errors import (
    UnsupportedLanguageError,
    ProviderError,
    BackupError,
    ValidationError,
    validate_symbol_name,
)
from .models.params import (
    AnalyzeParams,
    ExtractParams,
    FindParams,
    RenameParams,
    ShowParams,
)
from .models.responses import (
    AnalysisResult,
    ExtractResult,
    FindResult,
    RenameResult,
    ShowResult,
)
from .providers.base import RefactoringProvider
from .shared.backup import get_backup_manager
from .shared.logging import get_logger
from .shared.observability import track_operation

logger = get_logger(__name__)


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
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
    """Find project root by looking for markers"""
    current = Path(start_path).absolute()
    markers = [".git", "pyproject.toml", "setup.py", "Cargo.toml", "package.json"]

    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return str(current)
        current = current.parent

    return str(Path(start_path).absolute())


class RefactoringEngine:
    """Central registry and router for refactoring providers with enhanced features"""

    def __init__(self):
        self.providers: List[RefactoringProvider] = []
        self._language_cache: Dict[str, Optional[RefactoringProvider]] = {}
        self.backup_manager = get_backup_manager()
        self._destructive_operations = {"rename_symbol", "extract_element"}
        
        # Enhanced features
        self._provider_metrics: Dict[str, Dict[str, Any]] = {}
        self._provider_health: Dict[str, float] = {}
        self._operation_history: List[Dict[str, Any]] = []

    def register_provider(self, provider: RefactoringProvider) -> None:
        """Register a new refactoring provider"""
        logger.debug(f"Registering provider: {provider.__class__.__name__}")
        self.providers.append(provider)
        self._language_cache.clear()
        
        # Initialize metrics for the provider
        provider_name = getattr(provider, 'name', provider.__class__.__name__)
        self._provider_metrics[provider_name] = {
            'call_count': 0,
            'failure_count': 0,
            'total_response_time': 0.0,
            'avg_response_time': 0.0
        }
        self._provider_health[provider_name] = 1.0

    def get_provider(self, language: str) -> Optional[RefactoringProvider]:
        """Get best provider for language (cached)"""
        if language not in self._language_cache:
            for provider in self.providers:
                if provider.supports_language(language):
                    self._language_cache[language] = provider
                    logger.debug(
                        f"Found provider {provider.__class__.__name__} for {language}"
                    )
                    break
            else:
                self._language_cache[language] = None
                logger.warning(f"No provider found for language: {language}")

        return self._language_cache[language]

    def get_capabilities(self, language: str) -> List[str]:
        """Get capabilities for a language"""
        provider = self.get_provider(language)
        if not provider:
            return []
        return provider.get_capabilities(language)

    def _validate_operation_params(self, operation: str, params: Any) -> None:
        """Validate operation parameters."""
        if operation == "rename_symbol" and hasattr(params, "new_name"):
            if not validate_symbol_name(params.new_name):
                raise ValidationError(
                    field="new_name",
                    value=params.new_name,
                    reason="Must be a valid identifier (letters, numbers, underscores only)",
                )

        # Validate file paths exist
        if hasattr(params, "file_path") and params.file_path:
            file_path = Path(params.file_path)
            if not file_path.exists():
                raise ValidationError(
                    field="file_path",
                    value=params.file_path,
                    reason="File does not exist",
                )
            if not file_path.is_file():
                raise ValidationError(
                    field="file_path",
                    value=params.file_path,
                    reason="Path is not a file",
                )

    def _get_affected_files(self, operation: str, params: Any) -> List[str]:
        """Get list of files that might be affected by operation."""
        # For the new symbol-based system, we don't have explicit file paths
        # The provider will determine the actual scope during operation
        # For now, return empty list to disable backup functionality
        return []

    def _create_operation_backup(self, operation_id: str, files: List[str]) -> bool:
        """Create backup for operation if needed."""
        if not files:
            return True

        try:
            self.backup_manager.create_backup(operation_id, files)
            logger.info(f"Created backup for operation {operation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup for {operation_id}: {e}")
            raise BackupError(operation_id, str(e))

    def _cleanup_operation(self, operation_id: str, success: bool) -> None:
        """Cleanup after operation completion."""
        if success:
            # Clean up backup on success
            self.backup_manager.cleanup_backup(operation_id)
            logger.debug(f"Cleaned up backup for successful operation {operation_id}")
        else:
            # Keep backup for manual recovery
            logger.warning(f"Keeping backup for failed operation {operation_id}")

    def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
        """Analyze symbol using appropriate provider"""
        operation = "analyze_symbol"

        with track_operation(operation, symbol=params.symbol_name) as metrics:
            # Validate parameters
            self._validate_operation_params(operation, params)

            # For AnalyzeParams, we only have symbol_name, no file_path
            # Provider will handle symbol resolution
            provider = self.get_provider("python")  # Default to python for now

            if not provider:
                raise UnsupportedLanguageError("python")

            logger.info(f"Analyzing symbol {params.symbol_name}")

            try:
                result = provider.analyze_symbol(params)
                metrics.metadata["symbols_found"] = len(getattr(result, "symbols", []))
                return result
            except Exception as e:
                raise ProviderError(provider.__class__.__name__, operation, e)

    def find_symbols(self, params: FindParams) -> FindResult:
        """Find symbols using appropriate provider"""
        operation = "find_symbols"

        with track_operation(operation, pattern=params.pattern) as metrics:
            # FindParams only has pattern, no file_path
            provider = self.get_provider("python")  # Default to python for now

            if not provider:
                raise UnsupportedLanguageError("python")

            logger.info(f"Finding symbols matching '{params.pattern}'")

            try:
                result = provider.find_symbols(params)
                metrics.metadata["matches_found"] = len(getattr(result, "matches", []))
                return result
            except Exception as e:
                raise ProviderError(provider.__class__.__name__, operation, e)

    def show_function(self, params: ShowParams) -> ShowResult:
        """Show function details using appropriate provider"""
        operation = "show_function"

        with track_operation(operation, function=params.function_name) as metrics:
            # Validate parameters
            self._validate_operation_params(operation, params)

            # ShowParams only has function_name, no file_path
            provider = self.get_provider("python")  # Default to python for now

            if not provider:
                raise UnsupportedLanguageError("python")

            logger.info(f"Showing function {params.function_name}")

            try:
                result = provider.show_function(params)
                metrics.metadata["extractable_elements"] = len(
                    getattr(result, "extractable_elements", [])
                )
                return result
            except Exception as e:
                raise ProviderError(provider.__class__.__name__, operation, e)

    def rename_symbol(self, params: RenameParams) -> RenameResult:
        """Rename symbol using appropriate provider"""
        operation = "rename_symbol"
        operation_id = str(uuid.uuid4())

        with track_operation(
            operation, old_name=params.symbol_name, new_name=params.new_name
        ) as metrics:
            # Validate parameters
            self._validate_operation_params(operation, params)

            # RenameParams has symbol_name and new_name
            provider = self.get_provider("python")  # Default to python for now

            if not provider:
                raise UnsupportedLanguageError("python")

            # Create backup for destructive operation
            affected_files = self._get_affected_files(operation, params)
            self._create_operation_backup(operation_id, affected_files)

            logger.info(f"Renaming symbol {params.symbol_name} to {params.new_name}")

            try:
                result = provider.rename_symbol(params)
                metrics.metadata["files_modified"] = len(
                    getattr(result, "modified_files", [])
                )

                # Clean up backup on success
                self._cleanup_operation(operation_id, success=True)

                return result
            except Exception as e:
                # Keep backup for manual recovery
                self._cleanup_operation(operation_id, success=False)
                logger.error(
                    f"Rename operation failed, backup preserved: {operation_id}"
                )
                raise ProviderError(provider.__class__.__name__, operation, e)

    def extract_element(self, params: ExtractParams) -> ExtractResult:
        """Extract element using appropriate provider"""
        operation = "extract_element"
        operation_id = str(uuid.uuid4())

        with track_operation(
            operation, source=params.source, new_name=params.new_name
        ) as metrics:
            # Validate parameters
            self._validate_operation_params(operation, params)

            # ExtractParams has source and new_name
            provider = self.get_provider("python")  # Default to python for now

            if not provider:
                raise UnsupportedLanguageError("python")

            # Create backup for destructive operation
            affected_files = self._get_affected_files(operation, params)
            self._create_operation_backup(operation_id, affected_files)

            logger.info(f"Extracting {params.source} as {params.new_name}")

            try:
                result = provider.extract_element(params)
                metrics.metadata["extracted_element"] = params.source

                # Clean up backup on success
                self._cleanup_operation(operation_id, success=True)

                return result
            except Exception as e:
                # Keep backup for manual recovery
                self._cleanup_operation(operation_id, success=False)
                logger.error(
                    f"Extract operation failed, backup preserved: {operation_id}"
                )
                raise ProviderError(provider.__class__.__name__, operation, e)

    # Enhanced provider selection and fallback methods
    
    def _get_sorted_providers(self, language: str, operation: str) -> List[RefactoringProvider]:
        """Get providers sorted by priority and health for a specific operation."""
        suitable_providers = []
        
        for provider in self.providers:
            if not provider.supports_language(language):
                continue
                
            capabilities = provider.get_capabilities(language)
            if operation not in capabilities:
                continue
                
            provider_name = getattr(provider, 'name', provider.__class__.__name__)
            priority = getattr(provider, 'priority', 100)
            health = self._provider_health.get(provider_name, 1.0)
            
            suitable_providers.append((provider, priority, health))
        
        # Sort by priority (lower is better), then by health (higher is better)
        suitable_providers.sort(key=lambda x: (x[1], -x[2]))
        
        return [provider for provider, _, _ in suitable_providers]
    
    def _execute_with_provider(self, provider: RefactoringProvider, operation: str, 
                              params: Any, operation_id: Optional[str] = None) -> Any:
        """Execute operation with a specific provider and track metrics."""
        provider_name = getattr(provider, 'name', provider.__class__.__name__)
        start_time = time.time()
        
        try:
            # Track the call
            self._provider_metrics[provider_name]['call_count'] += 1
            
            # Execute the operation
            result: Any
            if operation == 'analyze_symbol':
                result = provider.analyze_symbol(params)
            elif operation == 'find_symbols':
                result = provider.find_symbols(params)
            elif operation == 'show_function':
                result = provider.show_function(params)
            elif operation == 'rename_symbol':
                result = provider.rename_symbol(params)
            elif operation == 'extract_element':
                result = provider.extract_element(params)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Track success metrics
            response_time = time.time() - start_time
            metrics = self._provider_metrics[provider_name]
            metrics['total_response_time'] += response_time
            metrics['avg_response_time'] = metrics['total_response_time'] / metrics['call_count']
            
            # Update health (successful operation improves health slightly)
            current_health = self._provider_health[provider_name]
            self._provider_health[provider_name] = min(1.0, current_health + 0.01)
            
            logger.debug(f"Provider {provider_name} succeeded for {operation} in {response_time:.3f}s")
            return result
            
        except Exception as e:
            # Track failure metrics
            response_time = time.time() - start_time
            metrics = self._provider_metrics[provider_name]
            metrics['failure_count'] += 1
            metrics['total_response_time'] += response_time
            metrics['avg_response_time'] = metrics['total_response_time'] / metrics['call_count']
            
            # Update health (failure decreases health)
            failure_rate = metrics['failure_count'] / metrics['call_count']
            self._provider_health[provider_name] = max(0.0, 1.0 - failure_rate)
            
            logger.warning(f"Provider {provider_name} failed for {operation} in {response_time:.3f}s: {e}")
            raise e
    
    def _execute_with_fallback(self, language: str, operation: str, params: Any, 
                              operation_id: Optional[str] = None) -> Any:
        """Execute operation with fallback to alternative providers."""
        sorted_providers = self._get_sorted_providers(language, operation)
        
        if not sorted_providers:
            raise UnsupportedLanguageError(language)
        
        last_exception = None
        
        for provider in sorted_providers:
            try:
                return self._execute_with_provider(provider, operation, params, operation_id)
            except Exception as e:
                last_exception = e
                provider_name = getattr(provider, 'name', provider.__class__.__name__)
                logger.warning(f"Provider {provider_name} failed, trying next provider")
                continue
        
        # All providers failed
        if last_exception:
            raise ProviderError("all_providers", operation, last_exception)
        else:
            raise UnsupportedLanguageError(language)
    
    # Enhanced operation methods with fallback
    
    def analyze_symbol_with_fallback(self, params: AnalyzeParams) -> AnalysisResult:
        """Analyze symbol with intelligent provider selection and fallback."""
        operation = "analyze_symbol"
        
        with track_operation(operation, symbol=params.symbol_name) as metrics:
            self._validate_operation_params(operation, params)
            language = "python"  # Default for now, could be enhanced with file detection
            
            try:
                result = self._execute_with_fallback(language, operation, params)
                metrics.metadata['symbols_found'] = len(getattr(result, 'symbols', []))
                return result
            except Exception as e:
                if isinstance(e, (UnsupportedLanguageError, ProviderError)):
                    raise e
                raise ProviderError("unknown", operation, e)
    
    def find_symbols_with_fallback(self, params: FindParams) -> FindResult:
        """Find symbols with intelligent provider selection and fallback."""
        operation = "find_symbols"
        
        with track_operation(operation, pattern=params.pattern) as metrics:
            language = "python"  # Default for now
            
            try:
                result = self._execute_with_fallback(language, operation, params)
                metrics.metadata['matches_found'] = len(getattr(result, 'matches', []))
                return result
            except Exception as e:
                if isinstance(e, (UnsupportedLanguageError, ProviderError)):
                    raise e
                raise ProviderError("unknown", operation, e)
    
    def show_function_with_fallback(self, params: ShowParams) -> ShowResult:
        """Show function with intelligent provider selection and fallback."""
        operation = "show_function"
        
        with track_operation(operation, function=params.function_name) as metrics:
            self._validate_operation_params(operation, params)
            language = "python"  # Default for now
            
            try:
                result = self._execute_with_fallback(language, operation, params)
                metrics.metadata['extractable_elements'] = len(getattr(result, 'extractable_elements', []))
                return result
            except Exception as e:
                if isinstance(e, (UnsupportedLanguageError, ProviderError)):
                    raise e
                raise ProviderError("unknown", operation, e)
    
    def rename_symbol_with_fallback(self, params: RenameParams) -> RenameResult:
        """Rename symbol with intelligent provider selection and fallback."""
        operation = "rename_symbol"
        operation_id = str(uuid.uuid4())
        
        with track_operation(operation, old_name=params.symbol_name, new_name=params.new_name) as metrics:
            self._validate_operation_params(operation, params)
            language = "python"  # Default for now
            
            # Create backup for destructive operation
            affected_files = self._get_affected_files(operation, params)
            self._create_operation_backup(operation_id, affected_files)
            
            try:
                result = self._execute_with_fallback(language, operation, params, operation_id)
                metrics.metadata['files_modified'] = len(getattr(result, 'modified_files', []))
                
                # Clean up backup on success
                self._cleanup_operation(operation_id, success=True)
                return result
                
            except Exception as e:
                # Keep backup for manual recovery
                self._cleanup_operation(operation_id, success=False)
                logger.error(f"Rename operation failed, backup preserved: {operation_id}")
                
                if isinstance(e, (UnsupportedLanguageError, ProviderError)):
                    raise e
                raise ProviderError("unknown", operation, e)
    
    def extract_element_with_fallback(self, params: ExtractParams) -> ExtractResult:
        """Extract element with intelligent provider selection and fallback."""
        operation = "extract_element"
        operation_id = str(uuid.uuid4())
        
        with track_operation(operation, source=params.source, new_name=params.new_name) as metrics:
            self._validate_operation_params(operation, params)
            language = "python"  # Default for now
            
            # Create backup for destructive operation
            affected_files = self._get_affected_files(operation, params)
            self._create_operation_backup(operation_id, affected_files)
            
            try:
                result = self._execute_with_fallback(language, operation, params, operation_id)
                metrics.metadata['extracted_element'] = params.source
                
                # Clean up backup on success
                self._cleanup_operation(operation_id, success=True)
                return result
                
            except Exception as e:
                # Keep backup for manual recovery
                self._cleanup_operation(operation_id, success=False)
                logger.error(f"Extract operation failed, backup preserved: {operation_id}")
                
                if isinstance(e, (UnsupportedLanguageError, ProviderError)):
                    raise e
                raise ProviderError("unknown", operation, e)
    
    def analyze_symbol_with_language_detection(self, params: AnalyzeParams, file_path: str) -> AnalysisResult:
        """Analyze symbol with automatic language detection."""
        operation = "analyze_symbol"
        
        with track_operation(operation, symbol=params.symbol_name, file_path=file_path) as metrics:
            self._validate_operation_params(operation, params)
            language = detect_language(file_path)
            
            try:
                result = self._execute_with_fallback(language, operation, params)
                metrics.metadata['language'] = language
                metrics.metadata['symbols_found'] = len(getattr(result, 'symbols', []))
                return result
            except Exception as e:
                if isinstance(e, (UnsupportedLanguageError, ProviderError)):
                    raise e
                raise ProviderError("unknown", operation, e)
    
    # Provider metrics and health monitoring
    
    def get_provider_metrics(self, provider_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific provider."""
        if provider_name not in self._provider_metrics:
            return {}
        
        metrics = self._provider_metrics[provider_name].copy()
        metrics['health_score'] = self._provider_health.get(provider_name, 1.0)
        return metrics
    
    def get_all_provider_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for all providers."""
        result = {}
        for provider_name in self._provider_metrics:
            result[provider_name] = self.get_provider_metrics(provider_name)
        return result
    
    def reset_provider_health(self, provider_name: str) -> None:
        """Reset health score for a specific provider."""
        if provider_name in self._provider_health:
            self._provider_health[provider_name] = 1.0
        
        if provider_name in self._provider_metrics:
            self._provider_metrics[provider_name]['failure_count'] = 0


# Global engine instance
engine = RefactoringEngine()
