"""Tests for the RefactoringEngine with mock providers."""

import pytest
import tempfile
from pathlib import Path
from typing import List

from refactor_mcp.engine import RefactoringEngine, detect_language, find_project_root
from refactor_mcp.models.errors import (
    UnsupportedLanguageError, ValidationError, ProviderError, BackupError
)
from refactor_mcp.models.params import (
    AnalyzeParams, FindParams, ShowParams, RenameParams, ExtractParams
)
from refactor_mcp.models.responses import (
    AnalysisResult, FindResult, ShowResult, RenameResult, ExtractResult
)
from refactor_mcp.providers.base import RefactoringProvider


class MockProvider(RefactoringProvider):
    """Mock provider for testing engine behavior."""
    
    def __init__(self, supported_languages: List[str] = None, should_fail: bool = False):
        self.supported_languages = supported_languages or ['python']
        self.should_fail = should_fail
        self.call_history = []
    
    def supports_language(self, language: str) -> bool:
        return language in self.supported_languages
    
    def get_capabilities(self, language: str) -> List[str]:
        if language in self.supported_languages:
            return ["analyze_symbol", "find_symbols", "show_function", "rename_symbol", "extract_element"]
        return []
    
    def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
        self.call_history.append(('analyze_symbol', params))
        if self.should_fail:
            raise Exception("Mock provider failure")
        
        return AnalysisResult(
            success=True,
            symbol=params.symbol,
            file_path=params.file_path,
            symbol_type="function",
            definition_location={"line": 10, "column": 1},
            scope="module",
            references=[],
            extractable_elements=[]
        )
    
    def find_symbols(self, params: FindParams) -> FindResult:
        self.call_history.append(('find_symbols', params))
        if self.should_fail:
            raise Exception("Mock provider failure")
        
        return FindResult(
            success=True,
            pattern=params.pattern,
            matches=[],
            total_matches=0
        )
    
    def show_function(self, params: ShowParams) -> ShowResult:
        self.call_history.append(('show_function', params))
        if self.should_fail:
            raise Exception("Mock provider failure")
        
        return ShowResult(
            success=True,
            function_name=params.function_name,
            file_path=params.file_path,
            function_body="def test(): pass",
            extractable_elements=[]
        )
    
    def rename_symbol(self, params: RenameParams) -> RenameResult:
        self.call_history.append(('rename_symbol', params))
        if self.should_fail:
            raise Exception("Mock provider failure")
        
        return RenameResult(
            success=True,
            old_name=params.old_name,
            new_name=params.new_name,
            modified_files=[params.file_path],
            changes_made=1
        )
    
    def extract_element(self, params: ExtractParams) -> ExtractResult:
        self.call_history.append(('extract_element', params))
        if self.should_fail:
            raise Exception("Mock provider failure")
        
        return ExtractResult(
            success=True,
            element_type=params.element_type,
            extracted_name="extracted_function",
            original_file=params.file_path,
            modifications=[]
        )


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def test_function():\n    return 42\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def engine():
    """Create a fresh RefactoringEngine for each test."""
    return RefactoringEngine()


@pytest.fixture
def mock_provider():
    """Create a mock provider."""
    return MockProvider()


@pytest.fixture
def failing_provider():
    """Create a provider that always fails."""
    return MockProvider(should_fail=True)


class TestLanguageDetection:
    """Test language detection functionality."""
    
    def test_detect_python(self):
        assert detect_language("test.py") == "python"
    
    def test_detect_javascript(self):
        assert detect_language("test.js") == "javascript"
    
    def test_detect_typescript(self):
        assert detect_language("test.ts") == "typescript"
    
    def test_detect_unknown(self):
        assert detect_language("test.xyz") == "unknown"
    
    def test_detect_case_insensitive(self):
        assert detect_language("TEST.PY") == "python"


class TestProjectRootDetection:
    """Test project root detection."""
    
    def test_find_project_root_with_git(self, tmp_path):
        # Create a git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        # Create a subdirectory
        sub_dir = tmp_path / "src" / "subdir"
        sub_dir.mkdir(parents=True)
        
        root = find_project_root(str(sub_dir))
        assert root == str(tmp_path)
    
    def test_find_project_root_with_pyproject(self, tmp_path):
        # Create pyproject.toml
        (tmp_path / "pyproject.toml").touch()
        
        sub_dir = tmp_path / "src"
        sub_dir.mkdir()
        
        root = find_project_root(str(sub_dir))
        assert root == str(tmp_path)
    
    def test_find_project_root_no_markers(self, tmp_path):
        # No project markers
        root = find_project_root(str(tmp_path))
        assert root == str(tmp_path.absolute())


class TestEngineBasics:
    """Test basic engine functionality."""
    
    def test_register_provider(self, engine, mock_provider):
        engine.register_provider(mock_provider)
        assert len(engine.providers) == 1
        assert engine.providers[0] == mock_provider
    
    def test_get_provider_found(self, engine, mock_provider):
        engine.register_provider(mock_provider)
        provider = engine.get_provider("python")
        assert provider == mock_provider
    
    def test_get_provider_not_found(self, engine):
        provider = engine.get_provider("python")
        assert provider is None
    
    def test_get_provider_caching(self, engine, mock_provider):
        engine.register_provider(mock_provider)
        
        # First call
        provider1 = engine.get_provider("python")
        # Second call should use cache
        provider2 = engine.get_provider("python")
        
        assert provider1 == provider2 == mock_provider
    
    def test_get_capabilities(self, engine, mock_provider):
        engine.register_provider(mock_provider)
        capabilities = engine.get_capabilities("python")
        assert "analyze_symbol" in capabilities
    
    def test_get_capabilities_no_provider(self, engine):
        capabilities = engine.get_capabilities("python")
        assert capabilities == []


class TestOperationValidation:
    """Test operation parameter validation."""
    
    def test_validate_rename_symbol_invalid_name(self, engine, mock_provider, temp_python_file):
        # This test should show that Pydantic validation catches invalid names
        with pytest.raises(Exception):  # Pydantic ValidationError
            params = RenameParams(
                symbol_name="test_function",
                new_name="123invalid"  # Invalid identifier
            )
    
    def test_validate_file_not_exists(self, engine, mock_provider):
        engine.register_provider(mock_provider)
        
        params = AnalyzeParams(
            file_path="/nonexistent/file.py",
            symbol="test"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            engine.analyze_symbol(params)
        
        assert exc_info.value.error_type == "validation_failed"
        assert "file_path" in exc_info.value.details["field"]


class TestOperationExecution:
    """Test operation execution with providers."""
    
    def test_analyze_symbol_success(self, engine, mock_provider, temp_python_file):
        engine.register_provider(mock_provider)
        
        params = AnalyzeParams(
            file_path=temp_python_file,
            symbol="test_function"
        )
        
        result = engine.analyze_symbol(params)
        
        assert result.success is True
        assert result.symbol == "test_function"
        assert ('analyze_symbol', params) in mock_provider.call_history
    
    def test_find_symbols_success(self, engine, mock_provider):
        engine.register_provider(mock_provider)
        
        params = FindParams(
            pattern="test",
            file_path="test.py"
        )
        
        result = engine.find_symbols(params)
        
        assert result.success is True
        assert result.pattern == "test"
        assert ('find_symbols', params) in mock_provider.call_history
    
    def test_show_function_success(self, engine, mock_provider, temp_python_file):
        engine.register_provider(mock_provider)
        
        params = ShowParams(
            file_path=temp_python_file,
            function_name="test_function"
        )
        
        result = engine.show_function(params)
        
        assert result.success is True
        assert result.function_name == "test_function"
        assert ('show_function', params) in mock_provider.call_history


class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_unsupported_language_error(self, engine, temp_python_file):
        # No providers registered
        params = AnalyzeParams(
            file_path=temp_python_file,
            symbol="test"
        )
        
        with pytest.raises(UnsupportedLanguageError) as exc_info:
            engine.analyze_symbol(params)
        
        assert exc_info.value.error_type == "unsupported_language"
        assert "python" in exc_info.value.details["language"]
    
    def test_provider_error_handling(self, engine, failing_provider, temp_python_file):
        engine.register_provider(failing_provider)
        
        params = AnalyzeParams(
            file_path=temp_python_file,
            symbol="test"
        )
        
        with pytest.raises(ProviderError) as exc_info:
            engine.analyze_symbol(params)
        
        assert exc_info.value.error_type == "operation_failed"
        assert "MockProvider" in exc_info.value.details["provider"]
        assert "analyze_symbol" in exc_info.value.details["operation"]


class TestBackupAndRecovery:
    """Test backup and recovery functionality."""
    
    def test_rename_with_backup(self, engine, mock_provider, temp_python_file):
        engine.register_provider(mock_provider)
        
        params = RenameParams(
            file_path=temp_python_file,
            old_name="test_function",
            new_name="renamed_function"
        )
        
        result = engine.rename_symbol(params)
        
        assert result.success is True
        # Backup should be cleaned up on success
        backups = engine.backup_manager.list_backups()
        assert len(backups) == 0
    
    def test_extract_with_backup(self, engine, mock_provider, temp_python_file):
        engine.register_provider(mock_provider)
        
        params = ExtractParams(
            file_path=temp_python_file,
            element_type="function",
            element_id="test_function"
        )
        
        result = engine.extract_element(params)
        
        assert result.success is True
        # Backup should be cleaned up on success
        backups = engine.backup_manager.list_backups()
        assert len(backups) == 0
    
    def test_backup_preserved_on_failure(self, engine, failing_provider, temp_python_file):
        engine.register_provider(failing_provider)
        
        params = RenameParams(
            file_path=temp_python_file,
            old_name="test_function",
            new_name="renamed_function"
        )
        
        with pytest.raises(ProviderError):
            engine.rename_symbol(params)
        
        # Backup should be preserved on failure
        backups = engine.backup_manager.list_backups()
        assert len(backups) == 1
        
        # Cleanup for test
        for backup in backups:
            engine.backup_manager.cleanup_backup(backup["operation_id"])


class TestObservability:
    """Test operation tracking and metrics."""
    
    def test_operation_tracking(self, engine, mock_provider, temp_python_file):
        engine.register_provider(mock_provider)
        
        params = AnalyzeParams(
            file_path=temp_python_file,
            symbol="test_function"
        )
        
        # Get initial operation count
        initial_count = len(engine.backup_manager.backup_manager._tracker.operations)
        
        result = engine.analyze_symbol(params)
        
        # Should have tracked one operation
        operations = engine.backup_manager.backup_manager._tracker.operations
        assert len(operations) > initial_count
        
        # Find our operation
        analyze_ops = [op for op in operations if op.operation == "analyze_symbol"]
        assert len(analyze_ops) > 0
        
        last_op = analyze_ops[-1]
        assert last_op.success is True
        assert last_op.duration_ms is not None