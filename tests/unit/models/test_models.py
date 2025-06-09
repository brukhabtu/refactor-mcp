"""Tests for Pydantic data models."""

import pytest
from pydantic import ValidationError

from refactor_mcp.models import (
    Position,
    Range,
    AnalyzeParams,
    RenameParams,
    ExtractParams,
    FindParams,
    ShowParams,
    SymbolInfo,
    ElementInfo,
    ShowResult,
    FindResult,
    RenameResult,
    ExtractResult,
    AnalysisResult,
    BackupResult,
    ErrorResponse,
    create_error_response,
    validate_symbol_name,
    ERROR_SYMBOL_NOT_FOUND,
)
from tests.test_utils import (
    assert_valid_symbol_info,
    assert_valid_element_info,
    assert_successful_result,
    assert_error_result,
    assert_models_equal,
    create_symbol,
    create_element,
    unit_test,
)
from tests.mocks.builders import MockResultBuilder


@unit_test
class TestPosition:
    """Test Position model validation."""

    def test_valid_position(self):
        """Test valid position creation."""
        pos = Position(line=10, column=5)
        assert pos.line == 10
        assert pos.column == 5

    def test_line_must_be_positive(self):
        """Test that line must be >= 1."""
        with pytest.raises(ValidationError) as exc_info:
            Position(line=0, column=5)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_column_can_be_zero(self):
        """Test that column can be 0."""
        pos = Position(line=1, column=0)
        assert pos.column == 0

    def test_column_cannot_be_negative(self):
        """Test that column cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            Position(line=1, column=-1)
        assert "greater than or equal to 0" in str(exc_info.value)


class TestRange:
    """Test Range model validation."""

    def test_valid_range(self):
        """Test valid range creation."""
        start = Position(line=1, column=0)
        end = Position(line=5, column=10)
        range_obj = Range(start=start, end=end)
        assert range_obj.start == start
        assert range_obj.end == end


class TestParameterModels:
    """Test parameter model validation."""

    def test_analyze_params_valid(self):
        """Test valid AnalyzeParams."""
        params = AnalyzeParams(symbol_name="my_function")
        assert params.symbol_name == "my_function"

    def test_rename_params_valid(self):
        """Test valid RenameParams."""
        params = RenameParams(symbol_name="old_name", new_name="new_name")
        assert params.symbol_name == "old_name"
        assert params.new_name == "new_name"

    def test_rename_params_invalid_new_name(self):
        """Test RenameParams with invalid new_name."""
        with pytest.raises(ValidationError) as exc_info:
            RenameParams(symbol_name="old_name", new_name="123invalid")
        assert "String should match pattern" in str(exc_info.value)

    def test_rename_params_invalid_hyphen(self):
        """Test RenameParams rejects hyphenated names."""
        with pytest.raises(ValidationError):
            RenameParams(symbol_name="old_name", new_name="new-name")

    def test_rename_params_invalid_space(self):
        """Test RenameParams rejects names with spaces."""
        with pytest.raises(ValidationError):
            RenameParams(symbol_name="old_name", new_name="new name")

    def test_extract_params_valid(self):
        """Test valid ExtractParams."""
        params = ExtractParams(source="function.lambda_1", new_name="extracted_func")
        assert params.source == "function.lambda_1"
        assert params.new_name == "extracted_func"

    def test_extract_params_invalid_new_name(self):
        """Test ExtractParams with invalid new_name."""
        with pytest.raises(ValidationError):
            ExtractParams(source="source", new_name="123invalid")

    def test_find_params_valid(self):
        """Test valid FindParams."""
        params = FindParams(pattern="*user*")
        assert params.pattern == "*user*"

    def test_show_params_valid(self):
        """Test valid ShowParams."""
        params = ShowParams(function_name="process_data")
        assert params.function_name == "process_data"


@unit_test 
class TestResponseModels:
    """Test response model creation and serialization."""

    def test_symbol_info_creation(self):
        """Test SymbolInfo model creation."""
        symbol = SymbolInfo(
            name="my_func",
            qualified_name="module.my_func",
            type="function",
            definition_location="module.py:15",
            scope="global",
            docstring="A test function"
        )
        assert_valid_symbol_info(symbol, "my_func")
        assert symbol.qualified_name == "module.my_func"
        assert symbol.docstring == "A test function"

    def test_symbol_info_without_docstring(self):
        """Test SymbolInfo without docstring."""
        symbol = SymbolInfo(
            name="my_func",
            qualified_name="module.my_func",
            type="function",
            definition_location="module.py:15",
            scope="global"
        )
        assert_valid_symbol_info(symbol, "my_func")
        assert symbol.docstring is None

    def test_symbol_info_using_builder(self):
        """Test SymbolInfo creation using test utilities."""
        symbol = create_symbol("test_function", "function", 
                             qualified_name="test.test_function",
                             docstring="Test function")
        assert_valid_symbol_info(symbol, "test_function")
        assert symbol.docstring == "Test function"

    def test_element_info_creation(self):
        """Test ElementInfo model creation."""
        element = ElementInfo(
            id="lambda_1",
            type="lambda",
            code="lambda x: x > 0",
            location="module.py:20",
            extractable=True
        )
        assert element.id == "lambda_1"
        assert element.extractable is True

    def test_show_result_with_elements(self):
        """Test ShowResult with extractable elements."""
        element = ElementInfo(
            id="lambda_1",
            type="lambda",
            code="lambda x: x > 0",
            location="module.py:20",
            extractable=True
        )
        result = ShowResult(
            success=True,
            function_name="process_data",
            extractable_elements=[element]
        )
        assert result.success is True
        assert len(result.extractable_elements) == 1

    def test_show_result_empty_elements(self):
        """Test ShowResult with no extractable elements."""
        result = ShowResult(success=True, function_name="simple_func")
        assert result.extractable_elements == []

    def test_find_result_with_matches(self):
        """Test FindResult with symbol matches."""
        symbol = SymbolInfo(
            name="user_func",
            qualified_name="auth.user_func",
            type="function",
            definition_location="auth.py:10",
            scope="global"
        )
        result = FindResult(
            success=True,
            pattern="*user*",
            matches=[symbol],
            total_count=1
        )
        assert result.total_count == 1
        assert len(result.matches) == 1

    def test_rename_result_success(self):
        """Test successful RenameResult."""
        result = RenameResult(
            success=True,
            old_name="old_func",
            new_name="new_func",
            qualified_name="module.new_func",
            files_modified=["module.py", "test_module.py"],
            references_updated=5,
            backup_id="backup_123"
        )
        assert result.success is True
        assert result.references_updated == 5
        assert len(result.files_modified) == 2

    def test_rename_result_with_conflicts(self):
        """Test RenameResult with conflicts."""
        result = RenameResult(
            success=False,
            old_name="old_func",
            new_name="new_func",
            qualified_name="module.old_func",
            conflicts=["Conflict: name already exists in scope"]
        )
        assert result.success is False
        assert len(result.conflicts) == 1

    def test_extract_result_success(self):
        """Test successful ExtractResult."""
        result = ExtractResult(
            success=True,
            source="process_data.lambda_1",
            new_function_name="is_valid",
            extracted_code="def is_valid(x):\n    return x > 0",
            parameters=["x"],
            return_type="bool",
            files_modified=["module.py"],
            backup_id="backup_456"
        )
        assert result.success is True
        assert result.return_type == "bool"
        assert len(result.parameters) == 1

    def test_analysis_result_with_references(self):
        """Test AnalysisResult with references."""
        symbol = SymbolInfo(
            name="target_func",
            qualified_name="module.target_func",
            type="function",
            definition_location="module.py:25",
            scope="global"
        )
        result = AnalysisResult(
            success=True,
            symbol_info=symbol,
            references=["module.py", "test_module.py"],
            reference_count=3,
            refactoring_suggestions=["Consider extracting inner function"]
        )
        assert result.reference_count == 3
        assert len(result.refactoring_suggestions) == 1

    def test_backup_result_creation(self):
        """Test BackupResult creation."""
        result = BackupResult(
            success=True,
            backup_id="backup_789",
            files_backed_up=["module.py", "utils.py"],
            timestamp="2024-01-01T12:00:00Z"
        )
        assert result.backup_id == "backup_789"
        assert len(result.files_backed_up) == 2


class TestErrorHandling:
    """Test error models and validation utilities."""

    def test_error_response_creation(self):
        """Test ErrorResponse model creation."""
        error = ErrorResponse(
            error_type=ERROR_SYMBOL_NOT_FOUND,
            message="Symbol 'unknown_func' not found",
            suggestions=["Did you mean 'known_func'?"]
        )
        assert error.success is False
        assert error.error_type == ERROR_SYMBOL_NOT_FOUND
        assert len(error.suggestions) == 1

    def test_error_response_no_suggestions(self):
        """Test ErrorResponse without suggestions."""
        error = ErrorResponse(
            error_type="validation_failed",
            message="Invalid input"
        )
        assert error.suggestions == []

    def test_create_error_response_helper(self):
        """Test create_error_response helper function."""
        error = create_error_response(
            "test_error",
            "Test message",
            ["Suggestion 1", "Suggestion 2"]
        )
        assert isinstance(error, ErrorResponse)
        assert error.error_type == "test_error"
        assert len(error.suggestions) == 2

    def test_create_error_response_no_suggestions(self):
        """Test create_error_response without suggestions."""
        error = create_error_response("test_error", "Test message")
        assert error.suggestions == []

    def test_validate_symbol_name_valid(self):
        """Test validate_symbol_name with valid names."""
        assert validate_symbol_name("valid_name") is True
        assert validate_symbol_name("_private") is True
        assert validate_symbol_name("CamelCase") is True
        assert validate_symbol_name("name123") is True

    def test_validate_symbol_name_invalid(self):
        """Test validate_symbol_name with invalid names."""
        assert validate_symbol_name("123invalid") is False
        assert validate_symbol_name("invalid-name") is False
        assert validate_symbol_name("invalid name") is False
        assert validate_symbol_name("invalid.name") is False
        assert validate_symbol_name("") is False


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_position_json_serialization(self):
        """Test Position JSON serialization."""
        pos = Position(line=10, column=5)
        json_data = pos.model_dump()
        assert json_data == {"line": 10, "column": 5}

    def test_symbol_info_json_serialization(self):
        """Test SymbolInfo JSON serialization."""
        symbol = SymbolInfo(
            name="test_func",
            qualified_name="module.test_func",
            type="function",
            definition_location="module.py:10",
            scope="global"
        )
        json_data = symbol.model_dump()
        expected = {
            "name": "test_func",
            "qualified_name": "module.test_func",
            "type": "function",
            "definition_location": "module.py:10",
            "scope": "global",
            "docstring": None
        }
        assert json_data == expected

    def test_model_from_dict(self):
        """Test creating models from dictionaries."""
        data = {
            "symbol_name": "test_symbol",
            "new_name": "renamed_symbol"
        }
        params = RenameParams(**data)
        assert params.symbol_name == "test_symbol"
        assert params.new_name == "renamed_symbol"