"""Integration tests for models with RefactoringEngine and providers."""

import pytest
from typing import List

from refactor_mcp.models import (
    AnalyzeParams,
    RenameParams,
    ExtractParams,
    FindParams,
    ShowParams,
    SymbolInfo,
    ElementInfo,
    AnalysisResult,
    RenameResult,
    ExtractResult,
    FindResult,
    ShowResult,
    ErrorResponse,
    create_error_response,
    ERROR_SYMBOL_NOT_FOUND,
    ERROR_PROVIDER_NOT_FOUND,
)
from refactor_mcp.providers.base import RefactoringProvider


class MockPythonProvider:
    """Mock provider for testing integration with models."""
    
    def supports_language(self, language: str) -> bool:
        """Check if this provider handles the given language."""
        return language == "python"
    
    def get_capabilities(self, language: str) -> List[str]:
        """Return list of supported operations for language."""
        if language == "python":
            return ["analyze", "rename", "extract", "find", "show"]
        return []
    
    def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
        """Analyze symbol and return structured result."""
        if params.symbol_name == "nonexistent_symbol":
            return AnalysisResult(
                success=False,
                symbol_info=None,
                references=[],
                reference_count=0,
                refactoring_suggestions=[]
            )
        
        symbol_info = SymbolInfo(
            name=params.symbol_name,
            qualified_name=f"module.{params.symbol_name}",
            type="function",
            definition_location="module.py:10",
            scope="global",
            docstring="Test function"
        )
        
        return AnalysisResult(
            success=True,
            symbol_info=symbol_info,
            references=["module.py", "test_module.py"],
            reference_count=5,
            refactoring_suggestions=["Consider adding type hints"]
        )
    
    def find_symbols(self, params: FindParams) -> FindResult:
        """Find symbols matching pattern."""
        if params.pattern == "*user*":
            symbols = [
                SymbolInfo(
                    name="user_login",
                    qualified_name="auth.user_login",
                    type="function",
                    definition_location="auth.py:25",
                    scope="global"
                ),
                SymbolInfo(
                    name="User",
                    qualified_name="models.User",
                    type="class",
                    definition_location="models.py:10",
                    scope="global"
                )
            ]
            return FindResult(
                success=True,
                pattern=params.pattern,
                matches=symbols,
                total_count=2
            )
        
        return FindResult(
            success=True,
            pattern=params.pattern,
            matches=[],
            total_count=0
        )
    
    def show_function(self, params: ShowParams) -> ShowResult:
        """Show extractable elements in function."""
        if params.function_name == "complex_function":
            elements = [
                ElementInfo(
                    id="lambda_1",
                    type="lambda",
                    code="lambda x: x > 0",
                    location="module.py:15",
                    extractable=True
                ),
                ElementInfo(
                    id="expression_1",
                    type="expression",
                    code="x * 2 + y",
                    location="module.py:16",
                    extractable=True
                )
            ]
            return ShowResult(
                success=True,
                function_name=params.function_name,
                extractable_elements=elements
            )
        
        return ShowResult(
            success=True,
            function_name=params.function_name,
            extractable_elements=[]
        )
    
    def rename_symbol(self, params: RenameParams) -> RenameResult:
        """Rename symbol with conflict detection."""
        if params.new_name == "conflicting_name":
            return RenameResult(
                success=False,
                old_name=params.symbol_name,
                new_name=params.new_name,
                qualified_name=f"module.{params.symbol_name}",
                files_modified=[],
                references_updated=0,
                conflicts=["Name 'conflicting_name' already exists in scope"]
            )
        
        return RenameResult(
            success=True,
            old_name=params.symbol_name,
            new_name=params.new_name,
            qualified_name=f"module.{params.new_name}",
            files_modified=["module.py", "test_module.py"],
            references_updated=3,
            conflicts=[],
            backup_id="backup_123"
        )
    
    def extract_element(self, params: ExtractParams) -> ExtractResult:
        """Extract code element into new function."""
        if params.source == "invalid_source":
            return ExtractResult(
                success=False,
                source=params.source,
                new_function_name=params.new_name,
                extracted_code="",
                parameters=[],
                files_modified=[]
            )
        
        return ExtractResult(
            success=True,
            source=params.source,
            new_function_name=params.new_name,
            extracted_code=f"def {params.new_name}(x):\n    return x > 0",
            parameters=["x"],
            return_type="bool",
            files_modified=["module.py"],
            backup_id="backup_456"
        )


class TestProviderIntegration:
    """Test integration between models and provider interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = MockPythonProvider()
    
    def test_provider_supports_language(self):
        """Test provider language support."""
        assert self.provider.supports_language("python") is True
        assert self.provider.supports_language("javascript") is False
    
    def test_provider_capabilities(self):
        """Test provider capabilities reporting."""
        capabilities = self.provider.get_capabilities("python")
        expected = ["analyze", "rename", "extract", "find", "show"]
        assert capabilities == expected
        
        assert self.provider.get_capabilities("unknown") == []
    
    def test_analyze_symbol_success(self):
        """Test successful symbol analysis with models."""
        params = AnalyzeParams(symbol_name="test_function")
        result = self.provider.analyze_symbol(params)
        
        assert isinstance(result, AnalysisResult)
        assert result.success is True
        assert result.symbol_info is not None
        assert result.symbol_info.name == "test_function"
        assert result.symbol_info.qualified_name == "module.test_function"
        assert result.reference_count == 5
        assert len(result.refactoring_suggestions) == 1
    
    def test_analyze_symbol_not_found(self):
        """Test symbol analysis when symbol not found."""
        params = AnalyzeParams(symbol_name="nonexistent_symbol")
        result = self.provider.analyze_symbol(params)
        
        assert isinstance(result, AnalysisResult)
        assert result.success is False
        assert result.symbol_info is None
        assert result.reference_count == 0
    
    def test_find_symbols_with_matches(self):
        """Test finding symbols with pattern matching."""
        params = FindParams(pattern="*user*")
        result = self.provider.find_symbols(params)
        
        assert isinstance(result, FindResult)
        assert result.success is True
        assert result.total_count == 2
        assert len(result.matches) == 2
        assert result.matches[0].name == "user_login"
        assert result.matches[1].name == "User"
    
    def test_find_symbols_no_matches(self):
        """Test finding symbols with no matches."""
        params = FindParams(pattern="*nonexistent*")
        result = self.provider.find_symbols(params)
        
        assert isinstance(result, FindResult)
        assert result.success is True
        assert result.total_count == 0
        assert len(result.matches) == 0
    
    def test_show_function_with_elements(self):
        """Test showing function with extractable elements."""
        params = ShowParams(function_name="complex_function")
        result = self.provider.show_function(params)
        
        assert isinstance(result, ShowResult)
        assert result.success is True
        assert len(result.extractable_elements) == 2
        assert result.extractable_elements[0].id == "lambda_1"
        assert result.extractable_elements[0].extractable is True
    
    def test_show_function_no_elements(self):
        """Test showing function with no extractable elements."""
        params = ShowParams(function_name="simple_function")
        result = self.provider.show_function(params)
        
        assert isinstance(result, ShowResult)
        assert result.success is True
        assert len(result.extractable_elements) == 0
    
    def test_rename_symbol_success(self):
        """Test successful symbol renaming."""
        params = RenameParams(symbol_name="old_function", new_name="new_function")
        result = self.provider.rename_symbol(params)
        
        assert isinstance(result, RenameResult)
        assert result.success is True
        assert result.old_name == "old_function"
        assert result.new_name == "new_function"
        assert result.references_updated == 3
        assert len(result.files_modified) == 2
        assert len(result.conflicts) == 0
        assert result.backup_id == "backup_123"
    
    def test_rename_symbol_with_conflicts(self):
        """Test symbol renaming with conflicts."""
        params = RenameParams(symbol_name="old_function", new_name="conflicting_name")
        result = self.provider.rename_symbol(params)
        
        assert isinstance(result, RenameResult)
        assert result.success is False
        assert len(result.conflicts) == 1
        assert "already exists in scope" in result.conflicts[0]
        assert result.references_updated == 0
    
    def test_extract_element_success(self):
        """Test successful element extraction."""
        params = ExtractParams(source="complex_function.lambda_1", new_name="is_positive")
        result = self.provider.extract_element(params)
        
        assert isinstance(result, ExtractResult)
        assert result.success is True
        assert result.new_function_name == "is_positive"
        assert "def is_positive" in result.extracted_code
        assert result.parameters == ["x"]
        assert result.return_type == "bool"
        assert result.backup_id == "backup_456"
    
    def test_extract_element_failure(self):
        """Test element extraction failure."""
        params = ExtractParams(source="invalid_source", new_name="extracted_func")
        result = self.provider.extract_element(params)
        
        assert isinstance(result, ExtractResult)
        assert result.success is False
        assert result.extracted_code == ""
        assert len(result.parameters) == 0


class TestModelValidationInProvider:
    """Test that provider operations properly validate input models."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = MockPythonProvider()
    
    def test_invalid_rename_parameters(self):
        """Test that invalid rename parameters are caught by Pydantic."""
        with pytest.raises(ValueError):  # Pydantic validation error
            RenameParams(symbol_name="valid", new_name="123invalid")
    
    def test_invalid_extract_parameters(self):
        """Test that invalid extract parameters are caught by Pydantic."""
        with pytest.raises(ValueError):  # Pydantic validation error
            ExtractParams(source="valid_source", new_name="invalid-name")
    
    def test_model_serialization_with_provider(self):
        """Test that provider results can be serialized to JSON."""
        params = AnalyzeParams(symbol_name="test_func")
        result = self.provider.analyze_symbol(params)
        
        # Test JSON serialization
        json_data = result.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["success"] is True
        assert json_data["symbol_info"]["name"] == "test_func"
    
    def test_model_deserialization_from_provider(self):
        """Test creating models from provider data."""
        # Simulate data coming from external source
        symbol_data = {
            "name": "external_func",
            "qualified_name": "external.external_func",
            "type": "function",
            "definition_location": "external.py:20",
            "scope": "global",
            "docstring": None
        }
        
        symbol = SymbolInfo(**symbol_data)
        assert symbol.name == "external_func"
        assert symbol.docstring is None


class TestErrorHandlingIntegration:
    """Test error handling integration with models."""
    
    def test_create_provider_error_response(self):
        """Test creating error responses for provider failures."""
        error = create_error_response(
            ERROR_SYMBOL_NOT_FOUND,
            "Symbol 'unknown_func' not found in project",
            ["Did you mean 'known_func'?", "Check spelling and imports"]
        )
        
        assert isinstance(error, ErrorResponse)
        assert error.success is False
        assert error.error_type == ERROR_SYMBOL_NOT_FOUND
        assert len(error.suggestions) == 2
    
    def test_provider_not_found_error(self):
        """Test error when no provider available."""
        error = create_error_response(
            ERROR_PROVIDER_NOT_FOUND,
            "No provider available for language: rust",
            ["Install rust-analyzer provider", "Use generic provider"]
        )
        
        assert error.error_type == ERROR_PROVIDER_NOT_FOUND
        assert "rust" in error.message


class TestModelConsistency:
    """Test model consistency across operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = MockPythonProvider()
    
    def test_symbol_info_consistency(self):
        """Test that SymbolInfo is consistent across operations."""
        # Find a symbol
        find_params = FindParams(pattern="*user*")
        find_result = self.provider.find_symbols(find_params)
        found_symbol = find_result.matches[0]
        
        # Analyze the same symbol
        analyze_params = AnalyzeParams(symbol_name=found_symbol.name)
        analyze_result = self.provider.analyze_symbol(analyze_params)
        analyzed_symbol = analyze_result.symbol_info
        
        # Symbol info should be consistent
        assert found_symbol.name == analyzed_symbol.name
        assert found_symbol.type == analyzed_symbol.type
    
    def test_operation_result_structure(self):
        """Test that all operation results have consistent structure."""
        # All results should have success field
        analyze_result = self.provider.analyze_symbol(AnalyzeParams(symbol_name="test"))
        find_result = self.provider.find_symbols(FindParams(pattern="test"))
        show_result = self.provider.show_function(ShowParams(function_name="test"))
        rename_result = self.provider.rename_symbol(RenameParams(symbol_name="test", new_name="new_test"))
        extract_result = self.provider.extract_element(ExtractParams(source="test", new_name="extracted"))
        
        for result in [analyze_result, find_result, show_result, rename_result, extract_result]:
            assert hasattr(result, 'success')
            assert isinstance(result.success, bool)
    
    def test_backup_id_consistency(self):
        """Test that backup IDs are provided for modifying operations."""
        # Rename operation
        rename_result = self.provider.rename_symbol(
            RenameParams(symbol_name="test", new_name="renamed")
        )
        if rename_result.success:
            assert rename_result.backup_id is not None
        
        # Extract operation
        extract_result = self.provider.extract_element(
            ExtractParams(source="test", new_name="extracted")
        )
        if extract_result.success:
            assert extract_result.backup_id is not None