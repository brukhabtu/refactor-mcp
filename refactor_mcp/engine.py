"""Central refactoring engine with provider registration and operation routing"""

import uuid
from pathlib import Path
from typing import Dict, List, Optional

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
    """Central registry and router for refactoring providers"""

    def __init__(self):
        self.providers: List[RefactoringProvider] = []
        self._language_cache: Dict[str, Optional[RefactoringProvider]] = {}
        self.backup_manager = get_backup_manager()
        self._destructive_operations = {"rename_symbol", "extract_element"}

    def register_provider(self, provider: RefactoringProvider) -> None:
        """Register a new refactoring provider"""
        logger.debug(f"Registering provider: {provider.__class__.__name__}")
        self.providers.append(provider)
        self._language_cache.clear()

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

    def _validate_operation_params(self, operation: str, params: any) -> None:
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

    def _get_affected_files(self, operation: str, params: any) -> List[str]:
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


# Global engine instance
engine = RefactoringEngine()
