"""True unit tests for RopeProvider - no file system or external dependencies."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import ast

from refactor_mcp.providers.rope.rope import RopeProvider
from refactor_mcp.models import (
    AnalyzeParams, FindParams, ShowParams, RenameParams, ExtractParams,
    AnalysisResult, FindResult, ShowResult, RenameResult, ExtractResult,
    SymbolInfo
)


class TestRopeProviderInterface:
    """Test RopeProvider interface and basic methods."""
    
    def setup_method(self):
        self.provider = RopeProvider()
    
    def test_supports_python_language(self):
        """Test language support detection."""
        assert self.provider.supports_language("python") is True
        assert self.provider.supports_language("javascript") is False
        assert self.provider.supports_language("unknown") is False
    
    def test_get_python_capabilities(self):
        """Test capability reporting for Python."""
        capabilities = self.provider.get_capabilities("python")
        expected = [
            "analyze_symbol", "find_symbols", "rename_symbol", 
            "extract_element", "show_function"
        ]
        assert set(capabilities) == set(expected)
    
    def test_get_no_capabilities_for_unsupported_language(self):
        """Test no capabilities for unsupported languages."""
        assert self.provider.get_capabilities("javascript") == []
        assert self.provider.get_capabilities("unknown") == []


class TestRopeProviderAnalyzeSymbol:
    """Test analyze_symbol method with mocked dependencies."""
    
    def setup_method(self):
        self.provider = RopeProvider()
    
    
    @patch('refactor_mcp.providers.rope.rope.find_project_root')
    @patch.object(RopeProvider, '_get_project')
    @patch.object(RopeProvider, '_resolve_symbol')
    def test_analyze_symbol_not_found(self, mock_resolve, mock_get_project, mock_find_root):
        """Test symbol not found scenario."""
        # Setup mocks
        mock_find_root.return_value = "/fake/project"
        mock_get_project.return_value = Mock()
        mock_resolve.return_value = None
        
        # Test
        params = AnalyzeParams(symbol_name="nonexistent_symbol")
        result = self.provider.analyze_symbol(params)
        
        # Assertions
        assert result.success is False
        assert result.error_type == "symbol_not_found"
        assert "nonexistent_symbol" in result.message


class TestRopeProviderFindSymbols:
    """Test find_symbols method with mocked dependencies."""
    
    def setup_method(self):
        self.provider = RopeProvider()
    
    @patch('refactor_mcp.providers.rope.rope.find_project_root')
    @patch.object(RopeProvider, '_get_project')
    @patch.object(RopeProvider, '_extract_module_symbols')
    def test_find_symbols_with_matches(self, mock_extract, mock_get_project, mock_find_root):
        """Test finding symbols with matches."""
        # Setup mocks
        mock_find_root.return_value = "/fake/project"
        mock_project = Mock()
        mock_resource = Mock()
        mock_resource.name = "module.py"
        mock_project.get_files.return_value = [mock_resource]
        mock_get_project.return_value = mock_project
        
        # Mock symbol extraction
        mock_symbols = [
            SymbolInfo(
                name="user_login",
                qualified_name="module.user_login", 
                type="function",
                definition_location="/fake/module.py:10",
                scope="global"
            ),
            SymbolInfo(
                name="user_logout",
                qualified_name="module.user_logout",
                type="function", 
                definition_location="/fake/module.py:20",
                scope="global"
            )
        ]
        mock_extract.return_value = mock_symbols
        
        # Test
        params = FindParams(pattern="user")
        result = self.provider.find_symbols(params)
        
        # Assertions
        assert result.success is True
        assert result.total_count == 2
        assert len(result.matches) == 2
        assert result.matches[0].name == "user_login"
        assert result.matches[1].name == "user_logout"
    
    @patch('refactor_mcp.providers.rope.rope.find_project_root')
    @patch.object(RopeProvider, '_get_project')
    def test_find_symbols_no_matches(self, mock_get_project, mock_find_root):
        """Test finding symbols with no matches."""
        # Setup mocks
        mock_find_root.return_value = "/fake/project"
        mock_project = Mock()
        mock_project.get_files.return_value = []
        mock_get_project.return_value = mock_project
        
        # Test
        params = FindParams(pattern="nonexistent")
        result = self.provider.find_symbols(params)
        
        # Assertions
        assert result.success is True
        assert result.total_count == 0
        assert len(result.matches) == 0


class TestRopeProviderHelperMethods:
    """Test helper methods with mocked dependencies."""
    
    def setup_method(self):
        self.provider = RopeProvider()
    
    def test_matches_pattern_exact(self):
        """Test pattern matching for exact matches."""
        assert self.provider._matches_pattern("hello", "hello") is True
        assert self.provider._matches_pattern("hello", "world") is False
    
    def test_matches_pattern_wildcard(self):
        """Test pattern matching with wildcards."""
        assert self.provider._matches_pattern("hello_world", "*world") is True
        assert self.provider._matches_pattern("hello_world", "hello*") is True
        assert self.provider._matches_pattern("hello_world", "*hello*") is True
        assert self.provider._matches_pattern("hello_world", "*xyz*") is False
    
    def test_matches_pattern_substring(self):
        """Test pattern matching for substrings."""
        assert self.provider._matches_pattern("hello_world", "world") is True
        assert self.provider._matches_pattern("hello_world", "hello") is True
        assert self.provider._matches_pattern("hello_world", "xyz") is False
    
    @patch.object(RopeProvider, '_find_resource')
    def test_resolve_symbol_cache_hit(self, mock_find_resource):
        """Test symbol resolution uses cache."""
        # Setup cache
        mock_project = Mock()
        mock_project.address = "/fake/project"
        cache_key = ("/fake/project", "test_symbol")
        cached_symbol = Mock()
        self.provider._symbol_cache[cache_key] = cached_symbol
        
        # Test
        result = self.provider._resolve_symbol(mock_project, "test_symbol")
        
        # Assertions
        assert result is cached_symbol
        mock_find_resource.assert_not_called()
    
    def test_parse_extraction_source_valid(self):
        """Test parsing valid extraction source."""
        result = self.provider._parse_extraction_source("module.function")
        assert result is not None
        assert result.module == "module"
        assert result.element == "function"
    
    def test_parse_extraction_source_complex(self):
        """Test parsing complex extraction source."""
        result = self.provider._parse_extraction_source("package.module.function")
        assert result is not None
        assert result.module == "package.module"
        assert result.element == "function"
    
    def test_parse_extraction_source_invalid(self):
        """Test parsing invalid extraction source."""
        result = self.provider._parse_extraction_source("invalid")
        assert result is None


class TestRopeProviderShowFunction:
    """Test show_function method with mocked dependencies."""
    
    def setup_method(self):
        self.provider = RopeProvider()
    
    @patch('refactor_mcp.providers.rope.rope.find_project_root')
    @patch.object(RopeProvider, '_get_project')
    @patch.object(RopeProvider, '_resolve_symbol')
    @patch.object(RopeProvider, '_find_extractable_elements')
    def test_show_function_success(self, mock_find_elements, mock_resolve, mock_get_project, mock_find_root):
        """Test successful function analysis."""
        # Setup mocks
        mock_find_root.return_value = "/fake/project"
        mock_get_project.return_value = Mock()
        
        mock_function = Mock()
        mock_function.type = "function"
        mock_resolve.return_value = mock_function
        
        from refactor_mcp.models import ElementInfo
        mock_elements = [
            ElementInfo(
                id="test_function.lambda_1",
                type="lambda",
                code="lambda x: x > 0",
                location="/fake/module.py:5",
                extractable=True
            )
        ]
        mock_find_elements.return_value = mock_elements
        
        # Test
        params = ShowParams(function_name="test_function")
        result = self.provider.show_function(params)
        
        # Assertions
        assert result.success is True
        assert result.function_name == "test_function"
        assert len(result.extractable_elements) == 1
        assert result.extractable_elements[0].type == "lambda"
    
    @patch('refactor_mcp.providers.rope.rope.find_project_root')
    @patch.object(RopeProvider, '_get_project')
    @patch.object(RopeProvider, '_resolve_symbol')
    def test_show_function_not_found(self, mock_resolve, mock_get_project, mock_find_root):
        """Test function not found scenario."""
        # Setup mocks
        mock_find_root.return_value = "/fake/project"
        mock_get_project.return_value = Mock()
        mock_resolve.return_value = None
        
        # Test
        params = ShowParams(function_name="nonexistent_function")
        result = self.provider.show_function(params)
        
        # Assertions
        assert result.success is False
        assert result.error_type == "function_not_found"
        assert "nonexistent_function" in result.message