"""
pytest configuration and shared fixtures for refactor-mcp tests.

This module provides:
- Global pytest configuration
- Shared fixtures for testing
- Test environment setup and teardown
- Common test data and mocking utilities
"""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

import pytest

from refactor_mcp.models import (
    SymbolInfo,
    ElementInfo,
    AnalysisResult,
    RenameResult,
    ExtractResult,
    FindResult,
    ShowResult,
    BackupResult,
    create_error_response,
)


# Test configuration
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# Directory and file fixtures
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_project_dir(temp_dir: Path) -> Path:
    """Create a test project directory with sample Python files."""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()
    
    # Create sample Python files
    (project_dir / "__init__.py").write_text("")
    
    (project_dir / "main.py").write_text('''
"""Main module for testing."""

def main():
    """Main function."""
    users = get_users()
    for user in users:
        process_user(user)

def get_users():
    """Get list of users."""
    return ["alice", "bob", "charlie"]

def process_user(user):
    """Process a single user."""
    valid = lambda x: len(x) > 0  # lambda for extraction testing
    if valid(user):
        print(f"Processing {user}")
    else:
        print("Invalid user")

class UserManager:
    """Class for managing users."""
    
    def __init__(self):
        self.users = []
    
    def add_user(self, name):
        """Add a user to the manager."""
        self.users.append(name)
    
    def remove_user(self, name):
        """Remove a user from the manager."""
        if name in self.users:
            self.users.remove(name)
''')
    
    (project_dir / "utils.py").write_text('''
"""Utility functions for testing."""

def format_name(first, last):
    """Format a full name."""
    return f"{first} {last}"

def validate_email(email):
    """Validate an email address."""
    return "@" in email and "." in email

def calculate_age(birth_year, current_year=2024):
    """Calculate age from birth year."""
    return current_year - birth_year

# Nested function for testing
def outer_function():
    """Function with nested elements."""
    def inner_function():
        """Nested function."""
        return "inner"
    
    items = [1, 2, 3]
    filtered = filter(lambda x: x > 1, items)  # lambda for testing
    return list(filtered)
''')
    
    (project_dir / "auth.py").write_text('''
"""Authentication utilities."""

def login(username, password):
    """Login function."""
    if not username or not password:
        return False
    return validate_credentials(username, password)

def validate_credentials(username, password):
    """Validate user credentials."""
    # Dummy validation for testing
    return len(username) > 3 and len(password) > 6

def logout(session_id):
    """Logout function."""
    # Clear session
    pass
''')
    
    return project_dir


@pytest.fixture
def empty_project_dir(temp_dir: Path) -> Path:
    """Create an empty project directory."""
    project_dir = temp_dir / "empty_project"
    project_dir.mkdir()
    return project_dir


# Mock provider fixtures
@pytest.fixture
def mock_provider():
    """Create a mock refactoring provider."""
    provider = Mock()
    provider.name = "mock_provider"
    provider.supports_language.return_value = True
    
    # Mock successful responses
    provider.analyze_symbol.return_value = AnalysisResult(
        success=True,
        symbol_info=SymbolInfo(
            name="test_function",
            qualified_name="module.test_function",
            type="function",
            definition_location="module.py:10",
            scope="global"
        ),
        references=["module.py:15", "test_module.py:5"],
        reference_count=2,
        refactoring_suggestions=["Consider extracting complex logic"]
    )
    
    provider.rename_symbol.return_value = RenameResult(
        success=True,
        old_name="old_function",
        new_name="new_function",
        qualified_name="module.new_function",
        files_modified=["module.py"],
        references_updated=3,
        backup_id="backup_123"
    )
    
    provider.extract_element.return_value = ExtractResult(
        success=True,
        source="function.lambda_1",
        new_function_name="extracted_lambda",
        extracted_code="def extracted_lambda(x):\n    return x > 0",
        parameters=["x"],
        return_type="bool",
        files_modified=["module.py"],
        backup_id="backup_456"
    )
    
    provider.find_symbols.return_value = FindResult(
        success=True,
        pattern="*test*",
        matches=[
            SymbolInfo(
                name="test_function",
                qualified_name="module.test_function",
                type="function",
                definition_location="module.py:10",
                scope="global"
            )
        ],
        total_count=1
    )
    
    provider.show_function.return_value = ShowResult(
        success=True,
        function_name="test_function",
        extractable_elements=[
            ElementInfo(
                id="lambda_1",
                type="lambda",
                code="lambda x: x > 0",
                location="module.py:15",
                extractable=True
            )
        ]
    )
    
    return provider


@pytest.fixture
def failing_provider():
    """Create a mock provider that returns errors."""
    provider = Mock()
    provider.name = "failing_provider"
    provider.supports_language.return_value = True
    
    # Mock error responses
    error_response = create_error_response(
        "symbol_not_found",
        "Symbol 'unknown_symbol' not found",
        ["Did you mean 'known_symbol'?"]
    )
    
    provider.analyze_symbol.return_value = error_response
    provider.rename_symbol.return_value = error_response
    provider.extract_element.return_value = error_response
    provider.find_symbols.return_value = error_response
    provider.show_function.return_value = error_response
    
    return provider


# Sample data fixtures
@pytest.fixture
def sample_symbol_info() -> SymbolInfo:
    """Create sample SymbolInfo for testing."""
    return SymbolInfo(
        name="sample_function",
        qualified_name="module.sample_function",
        type="function",
        definition_location="module.py:20",
        scope="global",
        docstring="A sample function for testing."
    )


@pytest.fixture
def sample_element_info() -> ElementInfo:
    """Create sample ElementInfo for testing."""
    return ElementInfo(
        id="lambda_1",
        type="lambda",
        code="lambda x: x > 0",
        location="module.py:25",
        extractable=True
    )


@pytest.fixture
def sample_analysis_result(sample_symbol_info: SymbolInfo) -> AnalysisResult:
    """Create sample AnalysisResult for testing."""
    return AnalysisResult(
        success=True,
        symbol_info=sample_symbol_info,
        references=["module.py:30", "test_module.py:10"],
        reference_count=2,
        refactoring_suggestions=["Consider adding type hints", "Extract complex logic"]
    )


@pytest.fixture
def sample_rename_result() -> RenameResult:
    """Create sample RenameResult for testing."""
    return RenameResult(
        success=True,
        old_name="old_function",
        new_name="new_function",
        qualified_name="module.new_function",
        files_modified=["module.py", "utils.py"],
        references_updated=5,
        backup_id="backup_789"
    )


@pytest.fixture
def sample_extract_result() -> ExtractResult:
    """Create sample ExtractResult for testing."""
    return ExtractResult(
        success=True,
        source="process_data.lambda_1",
        new_function_name="is_valid_data",
        extracted_code="def is_valid_data(data):\n    return data is not None",
        parameters=["data"],
        return_type="bool",
        files_modified=["module.py"],
        backup_id="backup_101"
    )


# Environment fixtures
@pytest.fixture
def mock_env():
    """Create a mock environment with controlled settings."""
    return {
        "REFACTOR_MCP_LOG_LEVEL": "DEBUG",
        "REFACTOR_MCP_BACKUP_DIR": "/tmp/refactor_backups",
        "REFACTOR_MCP_MAX_FILE_SIZE": "1000000"
    }


@pytest.fixture(autouse=True)
def isolate_tests(monkeypatch):
    """Automatically isolate tests from environment variables."""
    # Clear potentially interfering environment variables
    env_vars_to_clear = [
        "REFACTOR_MCP_LOG_LEVEL",
        "REFACTOR_MCP_BACKUP_DIR",
        "REFACTOR_MCP_CONFIG_FILE"
    ]
    
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)


# Helper fixtures for complex test scenarios
@pytest.fixture
def multi_file_project(temp_dir: Path) -> Path:
    """Create a multi-file project for complex refactoring tests."""
    project_dir = temp_dir / "multi_file_project"
    project_dir.mkdir()
    
    # Create package structure
    (project_dir / "__init__.py").write_text("")
    
    # Models module
    models_dir = project_dir / "models"
    models_dir.mkdir()
    (models_dir / "__init__.py").write_text("")
    (models_dir / "user.py").write_text('''
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
    
    def get_display_name(self):
        return self.name.title()
''')
    
    # Services module
    services_dir = project_dir / "services"
    services_dir.mkdir()
    (services_dir / "__init__.py").write_text("")
    (services_dir / "user_service.py").write_text('''
from ..models.user import User

class UserService:
    def __init__(self):
        self.users = []
    
    def create_user(self, name, email):
        user = User(name, email)
        self.users.append(user)
        return user
    
    def find_user_by_name(self, name):
        for user in self.users:
            if user.name == name:
                return user
        return None
''')
    
    # Main application
    (project_dir / "app.py").write_text('''
from .services.user_service import UserService

def main():
    service = UserService()
    user = service.create_user("John Doe", "john@example.com")
    found = service.find_user_by_name("John Doe")
    if found:
        print(found.get_display_name())

if __name__ == "__main__":
    main()
''')
    
    return project_dir


@pytest.fixture
def backup_manager():
    """Create a mock backup manager for testing."""
    manager = Mock()
    manager.create_backup.return_value = BackupResult(
        success=True,
        backup_id="test_backup_123",
        files_backed_up=["file1.py", "file2.py"],
        timestamp="2024-01-01T12:00:00Z"
    )
    manager.restore_backup.return_value = True
    manager.list_backups.return_value = ["test_backup_123", "test_backup_456"]
    return manager


# Parametrized test data
@pytest.fixture(params=[
    ("simple_function", "function"),
    ("SimpleClass", "class"),
    ("CONSTANT_VALUE", "variable"),
    ("_private_function", "function"),
])
def symbol_test_cases(request):
    """Parametrized test cases for different symbol types."""
    name, symbol_type = request.param
    return {
        "name": name,
        "type": symbol_type,
        "qualified_name": f"module.{name}",
        "definition_location": f"module.py:{hash(name) % 100 + 1}",
        "scope": "global" if not name.startswith("_") else "private"
    }