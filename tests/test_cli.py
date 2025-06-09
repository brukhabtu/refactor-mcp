"""Tests for CLI commands end-to-end integration."""

import pytest
import tempfile
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch

from refactor_mcp.cli import app
from refactor_mcp.models.responses import AnalysisResult, FindResult, RenameResult, SymbolInfo


@pytest.fixture
def temp_python_file():
    """Create a temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""def test_function():
    x = 42
    return x * 2

class TestClass:
    def method(self):
        return "hello"
""")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestAnalyzeCommand:
    """Test the analyze command."""
    
    def test_analyze_command_missing(self, runner):
        """Test that analyze command fails when not implemented."""
        result = runner.invoke(app, ["analyze", "test_function", "--file", "test.py"])
        assert result.exit_code != 0
    
    def test_analyze_command_success(self, runner, temp_python_file):
        """Test analyze command success path."""
        # Without providers, this should fail with an error message
        result = runner.invoke(app, ["analyze", "test_function", "--file", temp_python_file])
        assert result.exit_code == 1
        assert "No provider available" in result.stderr


class TestFindCommand:
    """Test the find command."""
    
    def test_find_command_missing(self, runner):
        """Test that find command fails when not implemented."""
        result = runner.invoke(app, ["find", "test"])
        assert result.exit_code != 0
    
    def test_find_command_success(self, runner, temp_python_file):
        """Test find command success path."""
        # Without providers, this should fail with an error message
        result = runner.invoke(app, ["find", "test", "--file", temp_python_file])
        assert result.exit_code == 1
        assert "No provider available" in result.stderr


class TestRenameCommand:
    """Test the rename command."""
    
    def test_rename_command_missing(self, runner):
        """Test that rename command fails when not implemented."""
        result = runner.invoke(app, ["rename", "old_name", "new_name", "--file", "test.py"])
        assert result.exit_code != 0
    
    def test_rename_command_success(self, runner, temp_python_file):
        """Test rename command success path."""
        # Without providers, this should fail with an error message
        result = runner.invoke(app, ["rename", "test_function", "renamed_function", "--file", temp_python_file])
        assert result.exit_code == 1
        assert "No provider available" in result.stderr


class TestCliEngineIntegration:
    """Test CLI integration with refactoring engine."""
    
    @patch('refactor_mcp.cli.engine')
    def test_analyze_uses_engine(self, mock_engine, runner, temp_python_file):
        """Test that analyze command uses the refactoring engine."""
        # Setup mock response
        symbol_info = SymbolInfo(
            name="test_function",
            qualified_name="module.test_function",
            type="function",
            definition_location=f"{temp_python_file}:1",
            scope="module"
        )
        mock_result = AnalysisResult(
            success=True,
            symbol_info=symbol_info,
            references=[temp_python_file],
            reference_count=1
        )
        mock_engine.analyze_symbol.return_value = mock_result
        
        # This will fail until we implement the command
        runner.invoke(app, ["analyze", "test_function", "--file", temp_python_file])
        
        # Verify engine was called
        mock_engine.analyze_symbol.assert_called_once()
        call_args = mock_engine.analyze_symbol.call_args[0][0]
        assert call_args.symbol == "test_function"
        assert call_args.file_path == temp_python_file
    
    @patch('refactor_mcp.cli.engine')
    def test_find_uses_engine(self, mock_engine, runner, temp_python_file):
        """Test that find command uses the refactoring engine."""
        # Setup mock response
        symbol_info = SymbolInfo(
            name="test_function",
            qualified_name="module.test_function",
            type="function",
            definition_location=f"{temp_python_file}:1",
            scope="module"
        )
        mock_result = FindResult(
            success=True,
            pattern="test",
            matches=[symbol_info],
            total_count=1
        )
        mock_engine.find_symbols.return_value = mock_result
        
        # This will fail until we implement the command
        runner.invoke(app, ["find", "test", "--file", temp_python_file])
        
        # Verify engine was called
        mock_engine.find_symbols.assert_called_once()
        call_args = mock_engine.find_symbols.call_args[0][0]
        assert call_args.pattern == "test"
    
    @patch('refactor_mcp.cli.engine')
    def test_rename_uses_engine(self, mock_engine, runner, temp_python_file):
        """Test that rename command uses the refactoring engine."""
        # Setup mock response
        mock_result = RenameResult(
            success=True,
            old_name="test_function",
            new_name="renamed_function",
            qualified_name="module.test_function",
            files_modified=[temp_python_file],
            references_updated=1
        )
        mock_engine.rename_symbol.return_value = mock_result
        
        # This will fail until we implement the command
        runner.invoke(app, ["rename", "test_function", "renamed_function", "--file", temp_python_file])
        
        # Verify engine was called
        mock_engine.rename_symbol.assert_called_once()
        call_args = mock_engine.rename_symbol.call_args[0][0]
        assert call_args.old_name == "test_function"
        assert call_args.new_name == "renamed_function"
        assert call_args.file_path == temp_python_file


class SimpleTestProvider:
    """Simple test provider for real file integration tests."""
    
    def supports_language(self, language: str) -> bool:
        return language == "python"
    
    def get_capabilities(self, language: str) -> list:
        return ["analyze_symbol", "find_symbols", "rename_symbol", "show_function", "extract_element"]
    
    def analyze_symbol(self, params):
        symbol_info = SymbolInfo(
            name=params.symbol,
            qualified_name=f"module.{params.symbol}",
            type="function",
            definition_location=f"{params.file_path}:1",
            scope="module"
        )
        return AnalysisResult(
            success=True,
            symbol_info=symbol_info,
            references=[params.file_path],
            reference_count=1
        )
    
    def find_symbols(self, params):
        symbol_info = SymbolInfo(
            name="test_function",
            qualified_name="module.test_function",
            type="function",
            definition_location=f"{params.file_path or 'test.py'}:1",
            scope="module"
        )
        return FindResult(
            success=True,
            pattern=params.pattern,
            matches=[symbol_info],
            total_count=1
        )
    
    def rename_symbol(self, params):
        return RenameResult(
            success=True,
            old_name=params.old_name,
            new_name=params.new_name,
            qualified_name=f"module.{params.old_name}",
            files_modified=[params.file_path],
            references_updated=1
        )
    
    def show_function(self, params):
        from refactor_mcp.models.responses import ShowResult
        return ShowResult(
            success=True,
            function_name=params.function_name,
            extractable_elements=[]
        )
    
    def extract_element(self, params):
        from refactor_mcp.models.responses import ExtractResult
        return ExtractResult(
            success=True,
            source=f"{params.element_type}.{params.element_id}",
            new_function_name="extracted_function",
            extracted_code="def extracted_function(): pass",
            files_modified=[params.file_path]
        )


class TestRealFileIntegration:
    """Test CLI commands with real providers and files."""
    
    def test_analyze_with_real_provider(self, runner, temp_python_file):
        """Test analyze command with a real provider registered."""
        from refactor_mcp.cli import engine
        
        # Register a simple test provider
        test_provider = SimpleTestProvider()
        original_providers = engine.providers[:]
        engine.register_provider(test_provider)
        
        try:
            result = runner.invoke(app, ["analyze", "test_function", "--file", temp_python_file])
            assert result.exit_code == 0
            assert "test_function" in result.stdout
            assert "function" in result.stdout
        finally:
            # Restore original providers
            engine.providers = original_providers
            engine._language_cache.clear()
    
    def test_find_with_real_provider(self, runner, temp_python_file):
        """Test find command with a real provider registered."""
        from refactor_mcp.cli import engine
        
        # Register a simple test provider
        test_provider = SimpleTestProvider()
        original_providers = engine.providers[:]
        engine.register_provider(test_provider)
        
        try:
            result = runner.invoke(app, ["find", "test", "--file", temp_python_file])
            assert result.exit_code == 0
            assert "Found" in result.stdout
            assert "test" in result.stdout
        finally:
            # Restore original providers
            engine.providers = original_providers
            engine._language_cache.clear()
    
    def test_rename_with_real_provider(self, runner, temp_python_file):
        """Test rename command with a real provider registered."""
        from refactor_mcp.cli import engine
        
        # Register a simple test provider
        test_provider = SimpleTestProvider()
        original_providers = engine.providers[:]
        engine.register_provider(test_provider)
        
        try:
            result = runner.invoke(app, ["rename", "test_function", "renamed_function", "--file", temp_python_file])
            assert result.exit_code == 0
            assert "Successfully renamed" in result.stdout
            assert "test_function" in result.stdout
            assert "renamed_function" in result.stdout
        finally:
            # Restore original providers
            engine.providers = original_providers
            engine._language_cache.clear()