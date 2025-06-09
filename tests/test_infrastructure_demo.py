"""
Demonstration of the comprehensive testing infrastructure.

This test file showcases how to use the various testing utilities,
fixtures, and mock providers for testing refactor-mcp functionality.
"""

import pytest
from pathlib import Path

from refactor_mcp.models import (
    AnalyzeParams,
    RenameParams,
    ExtractParams,
    FindParams,
    ShowParams,
    SymbolInfo,
    ElementInfo,
)
from tests.test_utils import (
    assert_valid_symbol_info,
    assert_valid_element_info,
    assert_successful_result,
    assert_error_result,
    create_symbol,
    create_element,
    FileManagerHelper,
    create_test_project_structure,
    unit_test,
    integration_test,
)
from tests.mocks.builders import (
    MockProviderBuilder,
    MockResultBuilder,
    ScenarioBuilderHelper,
)
from tests.mocks.providers import MockRopeProvider, FailingProvider
from tests.mocks.engines import MockRefactoringEngine, MockEngineBuilder


@unit_test
class TestMockInfrastructure:
    """Test the mock infrastructure itself."""
    
    def test_mock_provider_builder(self):
        """Test MockProviderBuilder functionality."""
        provider = (MockProviderBuilder("test_provider")
                   .supports_languages("python", "javascript")
                   .analyze_symbol_raises("unknown_symbol", "symbol_not_found", "Symbol not found")
                   .build())
        
        assert provider.name == "test_provider"
        assert provider.supports_language("python")
        assert provider.supports_language("javascript")
        assert not provider.supports_language("rust")
        
        # Test configured error response
        params = AnalyzeParams(symbol_name="unknown_symbol")
        result = provider.analyze_symbol(params)
        assert_error_result(result, "symbol_not_found")
    
    def test_mock_result_builder(self):
        """Test MockResultBuilder functionality."""
        # Test SymbolInfo builder
        symbol = (MockResultBuilder.symbol_info("test_func")
                 .type("function")
                 .scope("global")
                 .docstring("Test function")
                 .build())
        
        assert_valid_symbol_info(symbol, "test_func")
        assert symbol.docstring == "Test function"
        
        # Test ElementInfo builder
        element = (MockResultBuilder.element_info("lambda_1")
                  .type("lambda")
                  .code("lambda x: x > 0")
                  .extractable(True)
                  .build())
        
        assert_valid_element_info(element, "lambda")
        assert element.extractable is True
        
        # Test AnalysisResult builder
        analysis = (MockResultBuilder.analysis_result("test_symbol")
                   .with_references(["file1.py:10", "file2.py:20"])
                   .with_suggestions(["Add type hints", "Extract complex logic"])
                   .build())
        
        assert_successful_result(analysis)
        assert len(analysis.references) == 2
        assert len(analysis.refactoring_suggestions) == 2
    
    def test_test_scenario_builder(self):
        """Test TestScenarioBuilder functionality."""
        # Create a provider with specific responses
        provider = (MockProviderBuilder("scenario_provider")
                   .analyze_symbol_returns("target_func", 
                                          MockResultBuilder.analysis_result("target_func").build())
                   .build())
        
        # Build a complete test scenario
        scenario = (ScenarioBuilderHelper("analyze_scenario")
                   .with_provider(provider)
                   .with_mock_engine()
                   .expect_analyze_result("target_func", 
                                        MockResultBuilder.analysis_result("target_func").build())
                   .with_test_data("input_file", "test_module.py")
                   .build())
        
        assert scenario["name"] == "analyze_scenario"
        assert len(scenario["providers"]) == 1
        assert scenario["engine"] is not None
        assert "test_data" in scenario
        assert scenario["test_data"]["input_file"] == "test_module.py"


@unit_test  
class TestFileManagement:
    """Test file management utilities."""
    
    def test_test_file_manager(self, temp_dir):
        """Test TestFileManager functionality."""
        manager = FileManagerHelper(temp_dir)
        
        # Create files and directories
        test_file = manager.create_file("test.py", "print('hello')")
        test_dir = manager.create_directory("subdir")
        package_dir = manager.create_package("mypackage", "# Package init")
        
        assert test_file.exists()
        assert test_file.read_text() == "print('hello')"
        assert test_dir.exists()
        assert test_dir.is_dir()
        assert package_dir.exists()
        assert (package_dir / "__init__.py").exists()
        
        # Test Python file validation
        python_file = manager.create_python_file("valid", "def func(): pass")
        assert python_file.exists()
        
        # Test syntax validation
        with pytest.raises(ValueError, match="Invalid Python syntax"):
            manager.create_python_file("invalid", "def func( pass")
    
    def test_create_test_project_structure(self, temp_dir):
        """Test project structure creation utility."""
        structure = create_test_project_structure(temp_dir)
        
        assert "package" in structure
        assert "main" in structure
        assert "utils" in structure
        assert "manager" in structure
        
        # Verify files exist and have content
        assert structure["main"].exists()
        assert structure["utils"].exists()
        assert "def main():" in structure["main"].read_text()
        assert "def helper_function(" in structure["utils"].read_text()


@integration_test
class TestProviderIntegration:
    """Integration tests using mock providers."""
    
    def test_mock_rope_provider_analyze(self):
        """Test MockRopeProvider analyze functionality."""
        provider = MockRopeProvider()
        
        # Test successful analysis
        params = AnalyzeParams(symbol_name="get_user_info")
        result = provider.analyze_symbol(params)
        
        assert_successful_result(result)
        assert result.symbol_info.name == "get_user_info"
        assert len(result.references) > 0
        assert result.reference_count == len(result.references)
        
        # Test symbol not found
        params = AnalyzeParams(symbol_name="nonexistent_function")
        result = provider.analyze_symbol(params)
        
        assert_error_result(result, "symbol_not_found")
        assert "not found" in result.message.lower()
    
    def test_mock_rope_provider_rename(self):
        """Test MockRopeProvider rename functionality."""
        provider = MockRopeProvider()
        
        # Test successful rename
        params = RenameParams(symbol_name="get_user_info", new_name="get_user_data")
        result = provider.rename_symbol(params)
        
        assert_successful_result(result)
        assert result.old_name == "get_user_info"
        assert result.new_name == "get_user_data"
        assert len(result.files_modified) > 0
        assert result.references_updated > 0
        
        # Test conflict (rename to existing symbol)
        params = RenameParams(symbol_name="get_user_info", new_name="UserSession")
        result = provider.rename_symbol(params)
        
        assert not result.success
        assert len(result.conflicts) > 0
    
    def test_mock_rope_provider_extract(self):
        """Test MockRopeProvider extract functionality."""
        provider = MockRopeProvider()
        
        # Test successful extraction
        params = ExtractParams(source="get_user_info.lambda_1", new_name="is_valid_id")
        result = provider.extract_element(params)
        
        assert_successful_result(result)
        assert result.source == "get_user_info.lambda_1"
        assert result.new_function_name == "is_valid_id"
        assert len(result.parameters) > 0
        assert "def is_valid_id" in result.extracted_code
        
        # Test element not found
        params = ExtractParams(source="get_user_info.nonexistent", new_name="extracted")
        result = provider.extract_element(params)
        
        assert_error_result(result, "element_not_found")
    
    def test_failing_provider(self):
        """Test FailingProvider behavior."""
        provider = FailingProvider("test_error")
        
        # All operations should return errors
        analyze_result = provider.analyze_symbol(AnalyzeParams(symbol_name="any_symbol"))
        rename_result = provider.rename_symbol(RenameParams(symbol_name="old", new_name="new"))
        extract_result = provider.extract_element(ExtractParams(source="src", new_name="extracted"))
        find_result = provider.find_symbols(FindParams(pattern="*"))
        show_result = provider.show_function(ShowParams(function_name="func"))
        
        for result in [analyze_result, rename_result, extract_result, find_result, show_result]:
            assert_error_result(result, "test_error")


@integration_test
class TestEngineIntegration:
    """Integration tests using mock engines."""
    
    def test_mock_engine_with_multiple_providers(self):
        """Test MockRefactoringEngine with multiple providers."""
        engine = MockRefactoringEngine()
        
        # Verify default providers are registered
        assert "mock_rope" in engine.list_providers()
        assert "mock_tree_sitter" in engine.list_providers()
        assert engine.default_provider == "mock_rope"
        
        # Test provider switching
        assert engine.supports_language("python")
        assert engine.supports_language("javascript", "mock_tree_sitter")
        
        # Test operation routing
        params = AnalyzeParams(symbol_name="get_user_info")
        result = engine.analyze_symbol(params)
        
        assert_successful_result(result)
        
        # Check operation history
        history = engine.get_operation_history()
        assert len(history) == 1
        assert history[0][0] == "analyze"
        assert history[0][1] == "get_user_info"
    
    def test_mock_engine_builder(self):
        """Test MockEngineBuilder functionality."""
        engine = (MockEngineBuilder()
                 .with_rope_provider("/test/project")
                 .with_failing_provider("test_failure")
                 .with_default_provider("mock_rope")
                 .build())
        
        providers = engine.list_providers()
        assert "mock_rope" in providers
        assert "failing_provider" in providers
        assert engine.default_provider == "mock_rope"
        
        # Test that failing provider returns errors
        engine.set_default_provider("failing_provider")
        params = AnalyzeParams(symbol_name="any_symbol")
        result = engine.analyze_symbol(params)
        
        assert_error_result(result, "test_failure")


@unit_test
class TestUtilities:
    """Test utility functions."""
    
    def test_assertion_helpers(self):
        """Test assertion helper functions."""
        # Test valid symbol info
        symbol = create_symbol("test_func", "function")
        assert_valid_symbol_info(symbol, "test_func")
        
        # Test valid element info
        element = create_element("lambda_1", "lambda")
        assert_valid_element_info(element, "lambda")
        
        # Test successful result assertion
        analysis = MockResultBuilder.analysis_result("test").build()
        assert_successful_result(analysis)
        
        # Test error result assertion
        error = MockResultBuilder.error_response("test_error", "Test message").build()
        assert_error_result(error, "test_error")
    
    def test_parametrized_symbol_cases(self, symbol_test_cases):
        """Test using parametrized symbol test cases."""
        symbol = SymbolInfo(**symbol_test_cases)
        assert_valid_symbol_info(symbol)
        assert symbol.name == symbol_test_cases["name"]
        assert symbol.type == symbol_test_cases["type"]


@integration_test
class TestRealWorldScenarios:
    """Test realistic refactoring scenarios."""
    
    def test_complete_refactoring_workflow(self, test_project_dir):
        """Test a complete refactoring workflow."""
        engine = MockRefactoringEngine()
        
        # Step 1: Find symbols to refactor
        find_params = FindParams(pattern="*user*")
        find_result = engine.find_symbols(find_params)
        assert_successful_result(find_result)
        
        # Step 2: Analyze a specific symbol
        if find_result.matches:
            symbol_name = find_result.matches[0].name
            analyze_params = AnalyzeParams(symbol_name=symbol_name)
            analyze_result = engine.analyze_symbol(analyze_params)
            assert_successful_result(analyze_result)
        
        # Step 3: Show extractable elements
        show_params = ShowParams(function_name="get_user_info")
        show_result = engine.show_function(show_params)
        assert_successful_result(show_result)
        
        # Step 4: Extract an element if available
        if show_result.extractable_elements:
            element = show_result.extractable_elements[0]
            extract_params = ExtractParams(
                source=f"get_user_info.{element.id}",
                new_name="extracted_logic"
            )
            extract_result = engine.extract_element(extract_params)
            assert_successful_result(extract_result)
        
        # Verify operation history
        history = engine.get_operation_history()
        assert len(history) >= 3  # At least find, analyze, show operations
    
    def test_error_handling_workflow(self):
        """Test error handling in a workflow."""
        # Create engine with failing provider
        engine = (MockEngineBuilder()
                 .with_failing_provider("workflow_error")
                 .with_default_provider("failing_provider")
                 .build())
        
        # All operations should fail gracefully
        operations = [
            (engine.analyze_symbol, AnalyzeParams(symbol_name="test")),
            (engine.rename_symbol, RenameParams(symbol_name="old", new_name="new")),
            (engine.extract_element, ExtractParams(source="src", new_name="extracted")),
            (engine.find_symbols, FindParams(pattern="*")),
            (engine.show_function, ShowParams(function_name="func"))
        ]
        
        for operation_func, params in operations:
            result = operation_func(params)
            assert_error_result(result, "workflow_error")
            assert "workflow_error" in result.error_type
        
        # Verify all operations were tracked
        history = engine.get_operation_history()
        assert len(history) == len(operations)