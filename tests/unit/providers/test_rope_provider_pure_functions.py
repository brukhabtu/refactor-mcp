
def extracted_function():
    """Unit tests for RopeProvider - focused on pure functions and valuable logic."""

    from unittest.mock import Mock

    from refactor_mcp.providers.rope.rope import RopeProvider
    from refactor_mcp.models import AnalyzeParams


    class TestRopeProviderPureFunctions:
        """Test pure functions that have clear inputs/outputs and no side effects."""

        def setup_method(self):
            self.provider = RopeProvider()

        def test_create_analysis_result_success(self):
            """Test creating analysis result from symbol info - pure function."""
            # Create mock symbol info
            symbol_info = Mock()
            symbol_info.name = "test_function"
            symbol_info.type = "function"
            symbol_info.resource.path = "/fake/module.py"
            symbol_info.line = 10
            symbol_info.scope = "global"
            symbol_info.docstring = "Test docstring"

            # Create mock references
            ref1 = Mock()
            ref1.resource.path = "/fake/module.py"
            ref2 = Mock()
            ref2.resource.path = "/fake/other.py"
            references = [ref1, ref2]

            params = AnalyzeParams(symbol_name="test_function")
            suggestions = ["Consider extracting method"]

            # Test pure function
            result = self.provider._create_analysis_result(symbol_info, params, references, suggestions)

            # Assertions
            assert result.success is True
            assert result.symbol_info.name == "test_function"
            assert result.symbol_info.type == "function"
            assert result.symbol_info.qualified_name == "test_function"
            assert result.symbol_info.definition_location == "/fake/module.py:10"
            assert result.symbol_info.scope == "global"
            assert result.symbol_info.docstring == "Test docstring"
            assert result.reference_count == 2
            assert len(result.references) == 2
            assert "/fake/module.py" in result.references
            assert "/fake/other.py" in result.references
            assert result.refactoring_suggestions == ["Consider extracting method"]

        def test_create_analysis_result_empty_references(self):
            """Test creating analysis result with no references."""
            symbol_info = Mock()
            symbol_info.name = "isolated_function"
            symbol_info.type = "function"
            symbol_info.resource.path = "/fake/module.py"
            symbol_info.line = 5
            symbol_info.scope = "local"
            symbol_info.docstring = None

            params = AnalyzeParams(symbol_name="isolated_function")
            references = []
            suggestions = []

            result = self.provider._create_analysis_result(symbol_info, params, references, suggestions)

            assert result.success is True
            assert result.reference_count == 0
            assert result.references == []
            assert result.refactoring_suggestions == []
            assert result.symbol_info.docstring is None

        def test_matches_pattern_exact_match(self):
            """Test exact pattern matching - pure function."""
            assert self.provider._matches_pattern("hello", "hello") is True
            assert self.provider._matches_pattern("hello", "world") is False
            assert self.provider._matches_pattern("test_function", "test_function") is True

        def test_matches_pattern_substring_match(self):
            """Test substring pattern matching - pure function."""
            assert self.provider._matches_pattern("hello_world", "hello") is True
            assert self.provider._matches_pattern("hello_world", "world") is True
            assert self.provider._matches_pattern("hello_world", "xyz") is False
            assert self.provider._matches_pattern("getUserName", "user") is True

        def test_matches_pattern_wildcard_match(self):
            """Test wildcard pattern matching - pure function."""
            # Test * wildcard
            assert self.provider._matches_pattern("hello_world", "*world") is True
            assert self.provider._matches_pattern("hello_world", "hello*") is True
            assert self.provider._matches_pattern("hello_world", "*hello*") is True
            assert self.provider._matches_pattern("hello_world", "*xyz*") is False

            # Test ? wildcard
            assert self.provider._matches_pattern("hello", "hell?") is True
            assert self.provider._matches_pattern("hello", "h?llo") is True
            assert self.provider._matches_pattern("hello", "h?ll?") is True
            assert self.provider._matches_pattern("hello", "h??lo") is True  # h??lo matches hello (? = l, ? = l)

        def test_parse_extraction_source_valid_cases(self):
            """Test parsing extraction source strings - pure function."""
            # Simple case
            result = self.provider._parse_extraction_source("module.function")
            assert result is not None
            assert result.module == "module"
            assert result.element == "function"

            # Complex case
            result = self.provider._parse_extraction_source("package.submodule.class.method")
            assert result is not None
            assert result.module == "package.submodule.class"
            assert result.element == "method"

            # Nested case
            result = self.provider._parse_extraction_source("auth.utils.login.lambda_1")
            assert result is not None
            assert result.module == "auth.utils.login"
            assert result.element == "lambda_1"

        def test_parse_extraction_source_invalid_cases(self):
            """Test parsing invalid extraction source strings."""
            # Single word - no dot
            assert self.provider._parse_extraction_source("function") is None

            # Empty string
            assert self.provider._parse_extraction_source("") is None

            # Only dots
            assert self.provider._parse_extraction_source("...") is None

        def test_supports_language_boundary_cases(self):
            """Test language support with edge cases - pure function."""
            # Valid cases
            assert self.provider.supports_language("python") is True
            assert self.provider.supports_language("Python") is False  # Case sensitive
            assert self.provider.supports_language("PYTHON") is False

            # Invalid cases
            assert self.provider.supports_language("") is False
            assert self.provider.supports_language("javascript") is False
            assert self.provider.supports_language("rust") is False
            assert self.provider.supports_language(None) is False

        def test_get_capabilities_boundary_cases(self):
            """Test capability reporting with edge cases - pure function."""
            # Valid language
            capabilities = self.provider.get_capabilities("python")
            assert isinstance(capabilities, list)
            assert len(capabilities) == 5
            assert "analyze_symbol" in capabilities
            assert "find_symbols" in capabilities
            assert "rename_symbol" in capabilities
            assert "extract_element" in capabilities
            assert "show_function" in capabilities

            # Invalid languages
            assert self.provider.get_capabilities("") == []
            assert self.provider.get_capabilities("javascript") == []
            assert self.provider.get_capabilities(None) == []


    class TestRopeProviderCacheBehavior:
        """Test caching behavior which should be deterministic."""

        def setup_method(self):
            self.provider = RopeProvider()

        def test_symbol_cache_key_generation(self):
            """Test that cache keys are generated correctly."""
            # Setup cache manually to test behavior
            mock_project = Mock()
            mock_project.address = "/test/project"

            cache_key = ("/test/project", "test_symbol")
            mock_symbol = Mock()
            self.provider._symbol_cache[cache_key] = mock_symbol

            # Test cache retrieval
            result = self.provider._symbol_cache.get(cache_key)
            assert result is mock_symbol

            # Test different key doesn't match
            different_key = ("/test/project", "different_symbol")
            assert self.provider._symbol_cache.get(different_key) is None

        def test_clear_cache_resets_state(self):
            """Test that cache clearing works correctly."""
            # Add something to cache
            self.provider._symbol_cache[("test", "symbol")] = Mock()
            assert len(self.provider._symbol_cache) == 1

            # Clear cache
            self.provider._clear_cache()
            assert len(self.provider._symbol_cache) == 0

extracted_function()