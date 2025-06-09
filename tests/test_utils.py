"""
Testing utilities and helpers for refactor-mcp tests.

This module provides:
- Assertion helpers for model validation
- File system testing utilities
- Code comparison and validation tools
- Test data generation utilities
- Mock object builders
"""

import ast
import difflib
from pathlib import Path
from typing import Any, Dict, List, Union, Set
from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from refactor_mcp.models import (
    SymbolInfo,
    ElementInfo,
    AnalysisResult,
    RenameResult,
    ExtractResult,
    FindResult,
    ShowResult,
    ErrorResponse,
)


# Assertion helpers
def assert_valid_symbol_info(symbol: SymbolInfo, expected_name: str = None):
    """Assert that SymbolInfo is valid and optionally check name."""
    assert isinstance(symbol, SymbolInfo)
    assert symbol.name
    assert symbol.qualified_name
    assert symbol.type in ["function", "class", "variable", "method", "property"]
    assert symbol.definition_location
    assert symbol.scope in ["global", "local", "class", "function", "private"]
    
    if expected_name:
        assert symbol.name == expected_name


def assert_valid_element_info(element: ElementInfo, expected_type: str = None):
    """Assert that ElementInfo is valid and optionally check type."""
    assert isinstance(element, ElementInfo)
    assert element.id
    assert element.type
    assert element.code
    assert element.location
    assert isinstance(element.extractable, bool)
    
    if expected_type:
        assert element.type == expected_type


def assert_successful_result(result: Union[AnalysisResult, RenameResult, ExtractResult, FindResult, ShowResult]):
    """Assert that a result object indicates success."""
    assert hasattr(result, 'success')
    assert result.success is True
    assert not isinstance(result, ErrorResponse)


def assert_error_result(result: ErrorResponse, expected_error_type: str = None):
    """Assert that a result is an error with optional type check."""
    assert isinstance(result, ErrorResponse)
    assert result.success is False
    assert result.error_type
    assert result.message
    
    if expected_error_type:
        assert result.error_type == expected_error_type


def assert_models_equal(model1: BaseModel, model2: BaseModel, exclude_fields: Set[str] = None):
    """Assert that two Pydantic models are equal, optionally excluding fields."""
    exclude_fields = exclude_fields or set()
    
    dict1 = model1.model_dump(exclude=exclude_fields)
    dict2 = model2.model_dump(exclude=exclude_fields)
    
    assert dict1 == dict2, f"Models differ:\n{dict1}\nvs\n{dict2}"


# File system utilities
class FileManagerHelper:
    """Utility class for managing test files and directories."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.created_files: List[Path] = []
        self.created_dirs: List[Path] = []
    
    def create_file(self, relative_path: str, content: str = "") -> Path:
        """Create a file with given content."""
        file_path = self.base_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        self.created_files.append(file_path)
        return file_path
    
    def create_python_file(self, relative_path: str, content: str) -> Path:
        """Create a Python file and validate syntax."""
        if not relative_path.endswith('.py'):
            relative_path += '.py'
        
        # Validate Python syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax in {relative_path}: {e}")
        
        return self.create_file(relative_path, content)
    
    def create_directory(self, relative_path: str) -> Path:
        """Create a directory."""
        dir_path = self.base_dir / relative_path
        dir_path.mkdir(parents=True, exist_ok=True)
        self.created_dirs.append(dir_path)
        return dir_path
    
    def create_package(self, relative_path: str, init_content: str = "") -> Path:
        """Create a Python package with __init__.py."""
        package_dir = self.create_directory(relative_path)
        init_file = self.create_file(f"{relative_path}/__init__.py", init_content)
        return package_dir
    
    def list_files(self, pattern: str = "*") -> List[Path]:
        """List files matching pattern."""
        return list(self.base_dir.glob(pattern))
    
    def cleanup(self):
        """Clean up created files and directories."""
        for file_path in self.created_files:
            if file_path.exists():
                file_path.unlink()
        
        for dir_path in sorted(self.created_dirs, reverse=True):
            if dir_path.exists() and not any(dir_path.iterdir()):
                dir_path.rmdir()


# Code comparison utilities
def compare_python_code(code1: str, code2: str, ignore_whitespace: bool = True) -> bool:
    """Compare two Python code strings, optionally ignoring whitespace."""
    if ignore_whitespace:
        # Parse and unparse to normalize formatting
        try:
            tree1 = ast.parse(code1)
            tree2 = ast.parse(code2)
            return ast.dump(tree1) == ast.dump(tree2)
        except SyntaxError:
            # Fall back to string comparison if parsing fails
            pass
    
    return code1.strip() == code2.strip()


def get_code_diff(code1: str, code2: str, filename1: str = "before", filename2: str = "after") -> str:
    """Get a unified diff between two code strings."""
    lines1 = code1.splitlines(keepends=True)
    lines2 = code2.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        lines1, lines2,
        fromfile=filename1,
        tofile=filename2,
        lineterm=""
    )
    
    return "".join(diff)


def validate_python_syntax(code: str) -> bool:
    """Validate Python syntax without executing code."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def extract_functions_from_code(code: str) -> Dict[str, str]:
    """Extract function names and their code from Python source."""
    tree = ast.parse(code)
    functions = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Get the source code for this function
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1
            
            lines = code.splitlines()
            func_code = "\n".join(lines[start_line:end_line])
            functions[node.name] = func_code
    
    return functions


# Test data generators
class SymbolInfoBuilder:
    """Builder pattern for creating SymbolInfo test objects."""
    
    def __init__(self):
        self.data = {
            "name": "test_symbol",
            "qualified_name": "module.test_symbol",
            "type": "function",
            "definition_location": "module.py:10",
            "scope": "global"
        }
    
    def name(self, name: str) -> "SymbolInfoBuilder":
        """Set symbol name."""
        self.data["name"] = name
        return self
    
    def qualified_name(self, qualified_name: str) -> "SymbolInfoBuilder":
        """Set qualified name."""
        self.data["qualified_name"] = qualified_name
        return self
    
    def type(self, symbol_type: str) -> "SymbolInfoBuilder":
        """Set symbol type."""
        self.data["type"] = symbol_type
        return self
    
    def location(self, location: str) -> "SymbolInfoBuilder":
        """Set definition location."""
        self.data["definition_location"] = location
        return self
    
    def scope(self, scope: str) -> "SymbolInfoBuilder":
        """Set scope."""
        self.data["scope"] = scope
        return self
    
    def docstring(self, docstring: str) -> "SymbolInfoBuilder":
        """Set docstring."""
        self.data["docstring"] = docstring
        return self
    
    def build(self) -> SymbolInfo:
        """Build the SymbolInfo object."""
        return SymbolInfo(**self.data)


class ElementInfoBuilder:
    """Builder pattern for creating ElementInfo test objects."""
    
    def __init__(self):
        self.data = {
            "id": "element_1",
            "type": "lambda",
            "code": "lambda x: x",
            "location": "module.py:10",
            "extractable": True
        }
    
    def id(self, element_id: str) -> "ElementInfoBuilder":
        """Set element ID."""
        self.data["id"] = element_id
        return self
    
    def type(self, element_type: str) -> "ElementInfoBuilder":
        """Set element type."""
        self.data["type"] = element_type
        return self
    
    def code(self, code: str) -> "ElementInfoBuilder":
        """Set element code."""
        self.data["code"] = code
        return self
    
    def location(self, location: str) -> "ElementInfoBuilder":
        """Set element location."""
        self.data["location"] = location
        return self
    
    def extractable(self, extractable: bool) -> "ElementInfoBuilder":
        """Set extractable flag."""
        self.data["extractable"] = extractable
        return self
    
    def build(self) -> ElementInfo:
        """Build the ElementInfo object."""
        return ElementInfo(**self.data)


# Mock builders
class MockProviderBuilder:
    """Builder for creating mock refactoring providers."""
    
    def __init__(self):
        self.provider = Mock()
        self.provider.name = "mock_provider"
        self.provider.supports_language.return_value = True
    
    def with_name(self, name: str) -> "MockProviderBuilder":
        """Set provider name."""
        self.provider.name = name
        return self
    
    def supports_language(self, language: str, supported: bool = True) -> "MockProviderBuilder":
        """Configure language support."""
        if hasattr(self.provider.supports_language, 'side_effect'):
            # If already configured with side_effect, update it
            side_effect = self.provider.supports_language.side_effect or {}
        else:
            side_effect = {}
        
        side_effect[language] = supported
        self.provider.supports_language.side_effect = lambda lang: side_effect.get(lang, True)
        return self
    
    def analyze_returns(self, result: Union[AnalysisResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure analyze_symbol return value."""
        self.provider.analyze_symbol.return_value = result
        return self
    
    def rename_returns(self, result: Union[RenameResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure rename_symbol return value."""
        self.provider.rename_symbol.return_value = result
        return self
    
    def extract_returns(self, result: Union[ExtractResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure extract_element return value."""
        self.provider.extract_element.return_value = result
        return self
    
    def find_returns(self, result: Union[FindResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure find_symbols return value."""
        self.provider.find_symbols.return_value = result
        return self
    
    def show_returns(self, result: Union[ShowResult, ErrorResponse]) -> "MockProviderBuilder":
        """Configure show_function return value."""
        self.provider.show_function.return_value = result
        return self
    
    def build(self) -> Mock:
        """Build the mock provider."""
        return self.provider


# Common test patterns
def create_test_project_structure(base_dir: Path) -> Dict[str, Path]:
    """Create a standard test project structure."""
    manager = FileManagerHelper(base_dir)
    
    # Create main package
    package_dir = manager.create_package("myproject")
    
    # Create modules
    main_py = manager.create_python_file("myproject/main.py", '''
def main():
    """Main entry point."""
    print("Hello, World!")

if __name__ == "__main__":
    main()
''')
    
    utils_py = manager.create_python_file("myproject/utils.py", '''
def helper_function(data):
    """Helper function."""
    return data.strip() if data else ""

def format_output(text):
    """Format output text."""
    return f"Output: {text}"
''')
    
    # Create subpackage
    subpackage_dir = manager.create_package("myproject/submodule")
    worker_py = manager.create_python_file("myproject/submodule/worker.py", '''
class Worker:
    """Worker class."""
    
    def __init__(self, name):
        self.name = name
    
    def process(self, data):
        """Process data."""
        return f"{self.name}: {data}"
''')
    
    return {
        "package": package_dir,
        "main": main_py,
        "utils": utils_py,
        "subpackage": subpackage_dir,
        "worker": worker_py,
        "manager": manager
    }


# Test case generators
def generate_symbol_test_cases() -> List[Dict[str, Any]]:
    """Generate test cases for different symbol types."""
    return [
        {
            "name": "simple_function",
            "type": "function",
            "qualified_name": "module.simple_function",
            "scope": "global"
        },
        {
            "name": "MyClass",
            "type": "class",
            "qualified_name": "module.MyClass",
            "scope": "global"
        },
        {
            "name": "_private_function",
            "type": "function",
            "qualified_name": "module._private_function",
            "scope": "private"
        },
        {
            "name": "CONSTANT_VALUE",
            "type": "variable",
            "qualified_name": "module.CONSTANT_VALUE",
            "scope": "global"
        },
        {
            "name": "instance_method",
            "type": "method",
            "qualified_name": "module.MyClass.instance_method",
            "scope": "class"
        }
    ]


def generate_refactoring_test_cases() -> List[Dict[str, Any]]:
    """Generate test cases for refactoring operations."""
    return [
        {
            "operation": "rename",
            "old_name": "old_function",
            "new_name": "new_function",
            "expected_files": ["module.py"],
            "expected_references": 3
        },
        {
            "operation": "extract",
            "source": "process_data.lambda_1",
            "new_name": "is_valid",
            "expected_parameters": ["x"],
            "expected_return_type": "bool"
        },
        {
            "operation": "find",
            "pattern": "*user*",
            "expected_matches": ["user_function", "UserClass", "process_user"]
        }
    ]


# Convenience functions
def create_symbol(name: str, symbol_type: str = "function", **kwargs) -> SymbolInfo:
    """Convenience function to create a SymbolInfo."""
    builder = SymbolInfoBuilder().name(name).type(symbol_type)
    
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_element(element_id: str, element_type: str = "lambda", **kwargs) -> ElementInfo:
    """Convenience function to create an ElementInfo."""
    builder = ElementInfoBuilder().id(element_id).type(element_type)
    
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_mock_provider(name: str = "test_provider", **configs) -> Mock:
    """Convenience function to create a mock provider."""
    builder = MockProviderBuilder().with_name(name)
    
    for key, value in configs.items():
        method_name = f"{key}_returns"
        if hasattr(builder, method_name):
            getattr(builder, method_name)(value)
    
    return builder.build()


# Test decorators and markers
def requires_project_files(*files):
    """Decorator to mark tests that require specific project files."""
    def decorator(func):
        func._required_files = files
        return func
    return decorator


def slow_test(func):
    """Mark a test as slow."""
    return pytest.mark.slow(func)


def integration_test(func):
    """Mark a test as an integration test."""
    return pytest.mark.integration(func)


def unit_test(func):
    """Mark a test as a unit test."""
    return pytest.mark.unit(func)