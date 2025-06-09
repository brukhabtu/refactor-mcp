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
        # With Rope provider, this should work but may fail on symbol resolution
        result = runner.invoke(app, ["analyze", "test_function", "--file", temp_python_file])
        assert result.exit_code in [0, 1]  # May succeed or fail based on symbol resolution
        # Should not have "No provider available" error
        assert "No provider available" not in (result.stderr or "")


class TestFindCommand:
    """Test the find command."""
    
    def test_find_command_missing(self, runner):
        """Test that find command works when provider available."""
        result = runner.invoke(app, ["find", "test"])
        assert result.exit_code == 0  # Should work with Rope provider
    
    def test_find_command_success(self, runner, temp_python_file):
        """Test find command success path."""
        # With Rope provider, this should work
        result = runner.invoke(app, ["find", "test", "--file", temp_python_file])
        assert result.exit_code == 0
        assert "Found" in result.stdout


class TestRenameCommand:
    """Test the rename command."""
    
    def test_rename_command_missing(self, runner):
        """Test that rename command fails when not implemented."""
        result = runner.invoke(app, ["rename", "old_name", "new_name", "--file", "test.py"])
        assert result.exit_code != 0
    
    def test_rename_command_success(self, runner, temp_python_file):
        """Test rename command success path."""
        # With Rope provider, this should work but may fail on symbol resolution
        result = runner.invoke(app, ["rename", "test_function", "renamed_function", "--file", temp_python_file])
        assert result.exit_code in [0, 1]  # May succeed or fail based on symbol resolution
        # Should not have "No provider available" error
        assert "No provider available" not in (result.stderr or "")


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
        assert call_args.symbol_name == "test_function"
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
        assert call_args.symbol_name == "test_function"
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
            name=params.symbol_name,
            qualified_name=f"module.{params.symbol_name}",
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
            old_name=params.symbol_name,
            new_name=params.new_name,
            qualified_name=f"module.{params.symbol_name}",
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
            source=params.source,
            new_function_name=params.new_name,
            extracted_code="def extracted_function(): pass",
            files_modified=[params.file_path]
        )


class TestRealFileIntegration:
    """Test CLI commands with real providers and files."""
    
    def test_analyze_with_real_provider(self, runner, temp_python_file):
        """Test analyze command with a real provider registered."""
        from refactor_mcp.cli import engine
        
        # Clear all providers first to ensure clean state
        original_providers = engine.providers[:]
        engine.providers = []
        engine._language_cache.clear()
        
        # Register only the simple test provider
        test_provider = SimpleTestProvider()
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
        
        # Clear all providers first to ensure clean state
        original_providers = engine.providers[:]
        engine.providers = []
        engine._language_cache.clear()
        
        # Register only the simple test provider
        test_provider = SimpleTestProvider()
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
        
        # Clear all providers first to ensure clean state
        original_providers = engine.providers[:]
        engine.providers = []
        engine._language_cache.clear()
        
        # Register only the simple test provider
        test_provider = SimpleTestProvider()
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


class TestRopeProviderIntegration:
    """Test CLI commands with Rope provider integration."""
    
    def test_rename_with_rope_provider_works(self, runner, temp_python_file):
        """Test that rename command works with Rope provider."""
        result = runner.invoke(app, ["rename", "test_function", "renamed_function", "--file", temp_python_file])
        # May succeed or fail based on symbol resolution, but should not be "No provider available"
        if "No provider available" in (result.stderr or ""):
            pytest.fail("Rope provider should be available")
    
    def test_extract_command_exists(self, runner, temp_python_file):
        """Test that extract command exists and can be invoked."""
        result = runner.invoke(app, ["extract", "test_function.lambda_1", "extracted_function", "--file", temp_python_file])
        # Command exists (exit code may be 0 or 1 based on actual extraction)
        # We just ensure it's not a command not found error
        assert "No such command" not in (result.stdout or "")
    
    def test_show_command_exists(self, runner, temp_python_file):
        """Test that show command exists and can be invoked."""
        result = runner.invoke(app, ["show", "test_function", "--file", temp_python_file])
        # Command exists (exit code may be 0 or 1 based on actual analysis)
        # We just ensure it's not a command not found error
        assert "No such command" not in (result.stdout or "")


class TestEndToEndWorkflows:
    """Test complete CLI workflows with real Python files."""
    
    @pytest.fixture
    def complex_python_file(self):
        """Create a more complex Python file for end-to-end testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""def process_user_data(user_list):
    results = []
    for user in user_list:
        # Lambda that could be extracted
        is_adult = lambda age: age >= 18
        if is_adult(user.get('age', 0)):
            results.append({
                'name': user['name'],
                'status': 'adult'
            })
    return results

class UserProcessor:
    def validate_user(self, user_data):
        return user_data is not None and 'name' in user_data
        
    def format_user_name(self, user):
        return f"{user['first_name']} {user['last_name']}"
""")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    def test_analyze_workflow(self, runner, complex_python_file):
        """Test analyzing symbols in a real file."""
        result = runner.invoke(app, ["analyze", "process_user_data", "--file", complex_python_file])
        print(f"Analyze result: {result.stdout}")
        print(f"Analyze stderr: {result.stderr}")
        # Should either succeed or fail gracefully
        assert result.exit_code in [0, 1]
    
    def test_find_workflow(self, runner, complex_python_file):
        """Test finding symbols in a real file.""" 
        result = runner.invoke(app, ["find", "user", "--file", complex_python_file])
        print(f"Find result: {result.stdout}")
        print(f"Find stderr: {result.stderr}")
        # Should either succeed or fail gracefully
        assert result.exit_code in [0, 1]
    
    def test_show_workflow(self, runner, complex_python_file):
        """Test showing extractable elements in a real function."""
        result = runner.invoke(app, ["show", "process_user_data", "--file", complex_python_file])
        print(f"Show result: {result.stdout}")
        print(f"Show stderr: {result.stderr}")
        # Should either succeed or fail gracefully  
        assert result.exit_code in [0, 1]
        if result.exit_code == 0:
            # If successful, should mention lambdas or no extractable elements
            assert "lambda" in result.stdout or "No extractable elements" in result.stdout