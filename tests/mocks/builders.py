"""
Builder classes for creating mock objects and test data.

Provides fluent interfaces for constructing complex mock objects
and test scenarios with minimal boilerplate code.
"""

from typing import List, Dict, Any, Optional, Union, Callable
from unittest.mock import Mock

from refactor_mcp.models import (
    SymbolInfo,
    ElementInfo,
    AnalysisResult,
    RenameResult,
    ExtractResult,
    FindResult,
    ShowResult,
    ErrorResponse,
    create_error_response,
)
from .providers import ConfigurableProvider
from .engines import MockRefactoringEngine


class MockProviderBuilder:
    """
    Builder for creating mock refactoring providers with specific behaviors.
    
    Provides a fluent interface for configuring provider responses
    and behaviors for different test scenarios.
    """
    
    def __init__(self, name: str = "test_provider"):
        self.provider = ConfigurableProvider(name)
        self._language_support = {"python": True}
    
    def supports_languages(self, *languages: str) -> "MockProviderBuilder":
        """Configure which languages the provider supports."""
        self.provider.supported_languages = list(languages)
        for lang in languages:
            self._language_support[lang] = True
        return self
    
    def analyze_symbol_returns(self, symbol_name: str, result: Union[AnalysisResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure the response for analyzing a specific symbol."""
        self.provider.configure_analyze_response(symbol_name, result)
        return self
    
    def analyze_symbol_raises(self, symbol_name: str, error_type: str, message: str, suggestions: List[str] = None) -> "MockProviderBuilder":
        """Configure analyze_symbol to return an error for a specific symbol."""
        error = create_error_response(error_type, message, suggestions or [])
        return self.analyze_symbol_returns(symbol_name, error)
    
    def rename_symbol_returns(self, old_name: str, result: Union[RenameResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure the response for renaming a specific symbol."""
        self.provider.configure_rename_response(old_name, result)
        return self
    
    def rename_symbol_raises(self, old_name: str, error_type: str, message: str, suggestions: List[str] = None) -> "MockProviderBuilder":
        """Configure rename_symbol to return an error for a specific symbol."""
        error = create_error_response(error_type, message, suggestions or [])
        return self.rename_symbol_returns(old_name, error)
    
    def extract_element_returns(self, source: str, result: Union[ExtractResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure the response for extracting a specific element."""
        self.provider.configure_extract_response(source, result)
        return self
    
    def extract_element_raises(self, source: str, error_type: str, message: str, suggestions: List[str] = None) -> "MockProviderBuilder":
        """Configure extract_element to return an error for a specific source."""
        error = create_error_response(error_type, message, suggestions or [])
        return self.extract_element_returns(source, error)
    
    def find_symbols_returns(self, pattern: str, result: Union[FindResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure the response for finding symbols with a specific pattern."""
        self.provider.configure_find_response(pattern, result)
        return self
    
    def find_symbols_raises(self, pattern: str, error_type: str, message: str, suggestions: List[str] = None) -> "MockProviderBuilder":
        """Configure find_symbols to return an error for a specific pattern."""
        error = create_error_response(error_type, message, suggestions or [])
        return self.find_symbols_returns(pattern, error)
    
    def show_function_returns(self, function_name: str, result: Union[ShowResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure the response for showing a specific function."""
        self.provider.configure_show_response(function_name, result)
        return self
    
    def show_function_raises(self, function_name: str, error_type: str, message: str, suggestions: List[str] = None) -> "MockProviderBuilder":
        """Configure show_function to return an error for a specific function."""
        error = create_error_response(error_type, message, suggestions or [])
        return self.show_function_returns(function_name, error)
    
    def build(self) -> ConfigurableProvider:
        """Build the configured provider."""
        return self.provider


class MockResultBuilder:
    """
    Builder for creating mock result objects with realistic data.
    
    Simplifies creation of complex result objects for testing.
    """
    
    @staticmethod
    def symbol_info(name: str = "test_symbol") -> "SymbolInfoBuilder":
        """Create a SymbolInfo builder."""
        return SymbolInfoBuilder(name)
    
    @staticmethod
    def element_info(element_id: str = "element_1") -> "ElementInfoBuilder":
        """Create an ElementInfo builder."""
        return ElementInfoBuilder(element_id)
    
    @staticmethod
    def analysis_result(symbol_name: str = "test_symbol") -> "AnalysisResultBuilder":
        """Create an AnalysisResult builder."""
        return AnalysisResultBuilder(symbol_name)
    
    @staticmethod
    def rename_result(old_name: str = "old_name", new_name: str = "new_name") -> "RenameResultBuilder":
        """Create a RenameResult builder."""
        return RenameResultBuilder(old_name, new_name)
    
    @staticmethod
    def extract_result(source: str = "function.element", new_name: str = "extracted") -> "ExtractResultBuilder":
        """Create an ExtractResult builder."""
        return ExtractResultBuilder(source, new_name)
    
    @staticmethod
    def find_result(pattern: str = "*") -> "FindResultBuilder":
        """Create a FindResult builder."""
        return FindResultBuilder(pattern)
    
    @staticmethod
    def show_result(function_name: str = "test_function") -> "ShowResultBuilder":
        """Create a ShowResult builder."""
        return ShowResultBuilder(function_name)
    
    @staticmethod
    def error_response(error_type: str = "test_error", message: str = "Test error") -> "ErrorResponseBuilder":
        """Create an ErrorResponse builder."""
        return ErrorResponseBuilder(error_type, message)


class SymbolInfoBuilder:
    """Builder for SymbolInfo objects."""
    
    def __init__(self, name: str):
        self.data = {
            "name": name,
            "qualified_name": f"module.{name}",
            "type": "function",
            "definition_location": f"module.py:10",
            "scope": "global"
        }
    
    def qualified_name(self, qualified_name: str) -> "SymbolInfoBuilder":
        self.data["qualified_name"] = qualified_name
        return self
    
    def type(self, symbol_type: str) -> "SymbolInfoBuilder":
        self.data["type"] = symbol_type
        return self
    
    def location(self, location: str) -> "SymbolInfoBuilder":
        self.data["definition_location"] = location
        return self
    
    def scope(self, scope: str) -> "SymbolInfoBuilder":
        self.data["scope"] = scope
        return self
    
    def docstring(self, docstring: str) -> "SymbolInfoBuilder":
        self.data["docstring"] = docstring
        return self
    
    def build(self) -> SymbolInfo:
        return SymbolInfo(**self.data)


class ElementInfoBuilder:
    """Builder for ElementInfo objects."""
    
    def __init__(self, element_id: str):
        self.data = {
            "id": element_id,
            "type": "lambda",
            "code": "lambda x: x",
            "location": "module.py:15",
            "extractable": True
        }
    
    def type(self, element_type: str) -> "ElementInfoBuilder":
        self.data["type"] = element_type
        return self
    
    def code(self, code: str) -> "ElementInfoBuilder":
        self.data["code"] = code
        return self
    
    def location(self, location: str) -> "ElementInfoBuilder":
        self.data["location"] = location
        return self
    
    def extractable(self, extractable: bool) -> "ElementInfoBuilder":
        self.data["extractable"] = extractable
        return self
    
    def build(self) -> ElementInfo:
        return ElementInfo(**self.data)


class AnalysisResultBuilder:
    """Builder for AnalysisResult objects."""
    
    def __init__(self, symbol_name: str):
        self.symbol_info = SymbolInfoBuilder(symbol_name).build()
        self.data = {
            "success": True,
            "symbol_info": self.symbol_info,
            "references": [f"{symbol_name}_test.py:5"],
            "reference_count": 1,
            "refactoring_suggestions": []
        }
    
    def with_symbol_info(self, symbol_info: SymbolInfo) -> "AnalysisResultBuilder":
        self.data["symbol_info"] = symbol_info
        return self
    
    def with_references(self, references: List[str]) -> "AnalysisResultBuilder":
        self.data["references"] = references
        self.data["reference_count"] = len(references)
        return self
    
    def with_suggestions(self, suggestions: List[str]) -> "AnalysisResultBuilder":
        self.data["refactoring_suggestions"] = suggestions
        return self
    
    def success(self, success: bool) -> "AnalysisResultBuilder":
        self.data["success"] = success
        return self
    
    def build(self) -> AnalysisResult:
        return AnalysisResult(**self.data)


class RenameResultBuilder:
    """Builder for RenameResult objects."""
    
    def __init__(self, old_name: str, new_name: str):
        self.data = {
            "success": True,
            "old_name": old_name,
            "new_name": new_name,
            "qualified_name": f"module.{new_name}",
            "files_modified": ["module.py"],
            "references_updated": 1
        }
    
    def with_qualified_name(self, qualified_name: str) -> "RenameResultBuilder":
        self.data["qualified_name"] = qualified_name
        return self
    
    def with_files_modified(self, files: List[str]) -> "RenameResultBuilder":
        self.data["files_modified"] = files
        return self
    
    def with_references_updated(self, count: int) -> "RenameResultBuilder":
        self.data["references_updated"] = count
        return self
    
    def with_backup_id(self, backup_id: str) -> "RenameResultBuilder":
        self.data["backup_id"] = backup_id
        return self
    
    def with_conflicts(self, conflicts: List[str]) -> "RenameResultBuilder":
        self.data["conflicts"] = conflicts
        self.data["success"] = False
        return self
    
    def success(self, success: bool) -> "RenameResultBuilder":
        self.data["success"] = success
        return self
    
    def build(self) -> RenameResult:
        return RenameResult(**self.data)


class ExtractResultBuilder:
    """Builder for ExtractResult objects."""
    
    def __init__(self, source: str, new_name: str):
        self.data = {
            "success": True,
            "source": source,
            "new_function_name": new_name,
            "extracted_code": f"def {new_name}():\n    pass",
            "parameters": [],
            "return_type": "None",
            "files_modified": ["module.py"]
        }
    
    def with_extracted_code(self, code: str) -> "ExtractResultBuilder":
        self.data["extracted_code"] = code
        return self
    
    def with_parameters(self, parameters: List[str]) -> "ExtractResultBuilder":
        self.data["parameters"] = parameters
        return self
    
    def with_return_type(self, return_type: str) -> "ExtractResultBuilder":
        self.data["return_type"] = return_type
        return self
    
    def with_files_modified(self, files: List[str]) -> "ExtractResultBuilder":
        self.data["files_modified"] = files
        return self
    
    def with_backup_id(self, backup_id: str) -> "ExtractResultBuilder":
        self.data["backup_id"] = backup_id
        return self
    
    def success(self, success: bool) -> "ExtractResultBuilder":
        self.data["success"] = success
        return self
    
    def build(self) -> ExtractResult:
        return ExtractResult(**self.data)


class FindResultBuilder:
    """Builder for FindResult objects."""
    
    def __init__(self, pattern: str):
        self.data = {
            "success": True,
            "pattern": pattern,
            "matches": [],
            "total_count": 0
        }
    
    def with_matches(self, matches: List[SymbolInfo]) -> "FindResultBuilder":
        self.data["matches"] = matches
        self.data["total_count"] = len(matches)
        return self
    
    def success(self, success: bool) -> "FindResultBuilder":
        self.data["success"] = success
        return self
    
    def build(self) -> FindResult:
        return FindResult(**self.data)


class ShowResultBuilder:
    """Builder for ShowResult objects."""
    
    def __init__(self, function_name: str):
        self.data = {
            "success": True,
            "function_name": function_name,
            "extractable_elements": []
        }
    
    def with_elements(self, elements: List[ElementInfo]) -> "ShowResultBuilder":
        self.data["extractable_elements"] = elements
        return self
    
    def success(self, success: bool) -> "ShowResultBuilder":
        self.data["success"] = success
        return self
    
    def build(self) -> ShowResult:
        return ShowResult(**self.data)


class ErrorResponseBuilder:
    """Builder for ErrorResponse objects."""
    
    def __init__(self, error_type: str, message: str):
        self.data = {
            "error_type": error_type,
            "message": message,
            "suggestions": []
        }
    
    def with_suggestions(self, suggestions: List[str]) -> "ErrorResponseBuilder":
        self.data["suggestions"] = suggestions
        return self
    
    def build(self) -> ErrorResponse:
        return ErrorResponse(**self.data)


class ScenarioBuilderHelper:
    """
    Builder for creating complete test scenarios.
    
    Combines providers, engines, and expected results into
    cohesive test scenarios.
    """
    
    def __init__(self, scenario_name: str = "test_scenario"):
        self.scenario_name = scenario_name
        self.providers = []
        self.engine = None
        self.expected_results = {}
        self.test_data = {}
    
    def with_provider(self, provider) -> "ScenarioBuilderHelper":
        """Add a provider to the scenario."""
        self.providers.append(provider)
        return self
    
    def with_mock_engine(self) -> "ScenarioBuilderHelper":
        """Use a mock engine for the scenario."""
        self.engine = MockRefactoringEngine()
        return self
    
    def expect_analyze_result(self, symbol_name: str, result: Union[AnalysisResult, ErrorResponse]) -> "ScenarioBuilderHelper":
        """Set expected result for symbol analysis."""
        self.expected_results[("analyze", symbol_name)] = result
        return self
    
    def expect_rename_result(self, old_name: str, result: Union[RenameResult, ErrorResponse]) -> "ScenarioBuilderHelper":
        """Set expected result for symbol rename."""
        self.expected_results[("rename", old_name)] = result
        return self
    
    def expect_extract_result(self, source: str, result: Union[ExtractResult, ErrorResponse]) -> "ScenarioBuilderHelper":
        """Set expected result for element extraction."""
        self.expected_results[("extract", source)] = result
        return self
    
    def with_test_data(self, key: str, value: Any) -> "ScenarioBuilderHelper":
        """Add test data to the scenario."""
        self.test_data[key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the complete test scenario."""
        # Set up engine with providers
        if not self.engine:
            self.engine = MockRefactoringEngine()
        
        # Clear default providers and add our providers
        for provider_name in list(self.engine.providers.keys()):
            self.engine.unregister_provider(provider_name)
        
        for provider in self.providers:
            self.engine.register_provider(provider)
        
        return {
            "name": self.scenario_name,
            "engine": self.engine,
            "providers": self.providers,
            "expected_results": self.expected_results,
            "test_data": self.test_data
        }