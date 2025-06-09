"""Integration tests for multi-provider workflows"""

import pytest
from unittest.mock import Mock

from refactor_mcp.providers.registry import RefactoringEngine
from refactor_mcp.models.params import AnalyzeParams, RenameParams, ExtractParams, FindParams, ShowParams


class RopeProvider:
    """Mock rope provider for integration testing"""
    
    def __init__(self):
        self.name = "rope"
        self.priority = 3
        
    def supports_language(self, language: str) -> bool:
        return language == "python"
        
    def get_capabilities(self, language: str) -> list[str]:
        if language == "python":
            return ["analyze", "rename", "extract", "find", "show"]
        return []
        
    def is_healthy(self) -> bool:
        return True
        
    def analyze_symbol(self, params: AnalyzeParams):
        return Mock(
            success=True,
            symbol_name=params.symbol_name,
            symbol_type="function",
            location={"file": params.file_path, "line": 10, "column": 0},
            references=[],
            provider="rope"
        )
        
    def rename_symbol(self, params: RenameParams):
        return Mock(
            success=True,
            old_name=params.symbol_name,
            new_name=params.new_name,
            files_changed=1,
            provider="rope"
        )
        
    def extract_element(self, params: ExtractParams):
        return Mock(
            success=True,
            extracted_name=params.new_name,
            source_modified=True,
            provider="rope"
        )
        
    def find_symbols(self, params: FindParams):
        return Mock(
            success=True,
            matches=[{"name": "test_function", "file": "/test.py", "line": 5}],
            provider="rope"
        )
        
    def show_function(self, params: ShowParams):
        return Mock(
            success=True,
            extractable_elements=[
                {"id": "lambda_1", "type": "lambda", "line": 12},
                {"id": "block_1", "type": "code_block", "line": 15}
            ],
            provider="rope"
        )


class TreeSitterProvider:
    """Mock tree-sitter provider for integration testing"""
    
    def __init__(self):
        self.name = "tree-sitter"
        self.priority = 2
        
    def supports_language(self, language: str) -> bool:
        return language in ["python", "javascript", "typescript"]
        
    def get_capabilities(self, language: str) -> list[str]:
        if language in ["python", "javascript", "typescript"]:
            return ["analyze", "find"]  # Limited capabilities
        return []
        
    def is_healthy(self) -> bool:
        return True
        
    def analyze_symbol(self, params: AnalyzeParams):
        return Mock(
            success=True,
            symbol_name=params.symbol_name,
            symbol_type="function",
            location={"file": params.file_path, "line": 8, "column": 4},
            references=[],
            provider="tree-sitter"
        )
        
    def find_symbols(self, params: FindParams):
        return Mock(
            success=True,
            matches=[{"name": "test_func", "file": "/test.js", "line": 3}],
            provider="tree-sitter"
        )


class TestMultiProviderIntegration:
    """Test multi-provider integration scenarios"""
    
    def setup_method(self):
        """Setup fresh engine for each test"""
        self.engine = RefactoringEngine()
        self.rope_provider = RopeProvider()
        self.tree_sitter_provider = TreeSitterProvider()
        
    def test_provider_selection_by_capability(self):
        """Should select appropriate provider based on capabilities"""
        self.engine.register_provider(self.rope_provider, priority=3)
        self.engine.register_provider(self.tree_sitter_provider, priority=2)
        
        # For rename operation, should prefer rope (has capability)
        rename_providers = self.engine.get_providers_with_capability("python", "rename")
        assert len(rename_providers) == 1
        assert rename_providers[0] == self.rope_provider
        
        # For analyze operation, should return both (both have capability)
        analyze_providers = self.engine.get_providers_with_capability("python", "analyze")
        assert len(analyze_providers) == 2
        assert analyze_providers[0] == self.rope_provider  # Higher priority first
        assert analyze_providers[1] == self.tree_sitter_provider
        
    def test_cross_language_provider_selection(self):
        """Should select correct provider for different languages"""
        self.engine.register_provider(self.rope_provider, priority=3)
        self.engine.register_provider(self.tree_sitter_provider, priority=2)
        
        # Python: Should prefer rope
        python_provider = self.engine.get_best_provider("python")
        assert python_provider == self.rope_provider
        
        # JavaScript: Should use tree-sitter (only option)
        js_provider = self.engine.get_best_provider("javascript")
        assert js_provider == self.tree_sitter_provider
        
    def test_operation_execution_with_best_provider(self):
        """Should execute operations using best available provider"""
        self.engine.register_provider(self.rope_provider, priority=3)
        self.engine.register_provider(self.tree_sitter_provider, priority=2)
        
        # Analyze operation should use rope for Python
        params = AnalyzeParams(symbol_name="test_function", file_path="/test.py")
        result = self.engine.execute_operation("analyze_symbol", "python", params)
        
        assert result.success is True
        assert result.provider == "rope"
        
    def test_fallback_mechanism_integration(self):
        """Should fallback to secondary provider when primary fails"""
        # Create a failing rope provider
        failing_rope = Mock()
        failing_rope.supports_language.return_value = True
        failing_rope.get_capabilities.return_value = ["analyze", "rename"]
        failing_rope.is_healthy.return_value = False
        failing_rope.analyze_symbol.side_effect = RuntimeError("Rope failed")
        
        self.engine.register_provider(failing_rope, priority=3)
        self.engine.register_provider(self.tree_sitter_provider, priority=2)
        
        params = AnalyzeParams(symbol_name="test_function", file_path="/test.py")
        result = self.engine.execute_with_fallback("analyze_symbol", "python", params)
        
        assert result.success is True
        assert result.provider == "tree-sitter"  # Fell back to working provider
        
    def test_provider_caching_performance(self):
        """Should cache provider selections for performance"""
        self.engine.register_provider(self.rope_provider, priority=3)
        self.engine.register_provider(self.tree_sitter_provider, priority=2)
        
        # First call should populate cache
        provider1 = self.engine.get_best_provider("python")
        provider2 = self.engine.get_best_provider("python")
        
        assert provider1 == provider2 == self.rope_provider
        
        # Capabilities should also be cached
        caps1 = self.engine.get_cached_capabilities("python", self.rope_provider)
        caps2 = self.engine.get_cached_capabilities("python", self.rope_provider)
        
        assert caps1 == caps2
        
    def test_workflow_python_refactoring(self):
        """Test complete Python refactoring workflow"""
        self.engine.register_provider(self.rope_provider, priority=3)
        
        # Step 1: Find symbols
        find_params = FindParams(pattern="test_*", file_path="/test.py")
        find_result = self.engine.execute_operation("find_symbols", "python", find_params)
        assert find_result.success is True
        
        # Step 2: Analyze found symbol
        analyze_params = AnalyzeParams(symbol_name="test_function", file_path="/test.py")
        analyze_result = self.engine.execute_operation("analyze_symbol", "python", analyze_params)
        assert analyze_result.success is True
        
        # Step 3: Show extractable elements
        show_params = ShowParams(function_name="test_function", file_path="/test.py")
        show_result = self.engine.execute_operation("show_function", "python", show_params)
        assert show_result.success is True
        assert len(show_result.extractable_elements) > 0
        
        # Step 4: Extract element
        extract_params = ExtractParams(source="test_function.lambda_1", new_name="is_valid", file_path="/test.py")
        extract_result = self.engine.execute_operation("extract_element", "python", extract_params)
        assert extract_result.success is True
        
        # Step 5: Rename symbol
        rename_params = RenameParams(symbol_name="test_function", new_name="validate_input", file_path="/test.py")
        rename_result = self.engine.execute_operation("rename_symbol", "python", rename_params)
        assert rename_result.success is True
        
    def test_multi_language_project_support(self):
        """Test support for projects with multiple languages"""
        self.engine.register_provider(self.rope_provider, priority=3)
        self.engine.register_provider(self.tree_sitter_provider, priority=2)
        
        # Python file analysis
        py_params = AnalyzeParams(symbol_name="python_func", file_path="/src/app.py")
        py_result = self.engine.execute_operation("analyze_symbol", "python", py_params)
        assert py_result.provider == "rope"
        
        # JavaScript file analysis
        js_params = AnalyzeParams(symbol_name="jsFunction", file_path="/src/script.js")
        js_result = self.engine.execute_operation("analyze_symbol", "javascript", js_params)
        assert js_result.provider == "tree-sitter"
        
    def test_provider_health_monitoring(self):
        """Test provider health monitoring and recovery"""
        # Mock an unhealthy provider that becomes healthy
        flaky_provider = Mock()
        flaky_provider.supports_language.return_value = True
        flaky_provider.get_capabilities.return_value = ["analyze"]
        flaky_provider.is_healthy.side_effect = [False, False, True]  # Becomes healthy on 3rd check
        flaky_provider.analyze_symbol.return_value = Mock(success=True, provider="flaky")
        
        self.engine.register_provider(flaky_provider, priority=3)
        self.engine.register_provider(self.tree_sitter_provider, priority=2)
        
        # First check: Should return only healthy providers
        healthy = self.engine.get_healthy_providers("python")
        assert len(healthy) == 1
        assert healthy[0] == self.tree_sitter_provider
        
        # Second check: Still unhealthy
        healthy = self.engine.get_healthy_providers("python")
        assert len(healthy) == 1
        assert healthy[0] == self.tree_sitter_provider
        
        # Third check: Now healthy
        healthy = self.engine.get_healthy_providers("python")
        assert len(healthy) == 2
        assert flaky_provider in healthy


class TestRegistryGlobalState:
    """Test integration with global registry state"""
    
    def test_global_engine_instance(self):
        """Should maintain global engine state correctly"""
        from refactor_mcp.providers.registry import engine as global_engine
        
        # Register provider on global instance
        rope_provider = RopeProvider()
        global_engine.register_provider(rope_provider, priority=3)
        
        # Should be available from global instance
        provider = global_engine.get_best_provider("python")
        assert provider == rope_provider
        
        # Clean up
        global_engine._providers.clear()
        global_engine._clear_caches()
        
    def test_registry_state_isolation(self):
        """Should properly isolate different engine instances"""
        engine1 = RefactoringEngine()
        engine2 = RefactoringEngine()
        
        rope1 = RopeProvider()
        rope2 = RopeProvider()
        
        engine1.register_provider(rope1, priority=3)
        engine2.register_provider(rope2, priority=3)
        
        # Each engine should have its own providers
        assert engine1.get_best_provider("python") == rope1
        assert engine2.get_best_provider("python") == rope2
        assert engine1.get_best_provider("python") != engine2.get_best_provider("python")


class TestErrorHandlingIntegration:
    """Test error handling in integrated scenarios"""
    
    def test_no_suitable_provider_error(self):
        """Should handle cases where no provider supports operation"""
        engine = RefactoringEngine()
        
        # Only register provider that doesn't support the language
        limited_provider = Mock()
        limited_provider.supports_language.return_value = False
        engine.register_provider(limited_provider)
        
        with pytest.raises(RuntimeError, match="No provider available"):
            engine.execute_operation("analyze_symbol", "unsupported_language", Mock())
            
    def test_all_providers_unhealthy_error(self):
        """Should handle cases where all providers are unhealthy"""
        engine = RefactoringEngine()
        
        unhealthy1 = Mock()
        unhealthy1.supports_language.return_value = True
        unhealthy1.is_healthy.return_value = False
        unhealthy1.analyze_symbol.side_effect = RuntimeError("Unhealthy")
        
        unhealthy2 = Mock()
        unhealthy2.supports_language.return_value = True
        unhealthy2.is_healthy.return_value = False
        unhealthy2.analyze_symbol.side_effect = RuntimeError("Also unhealthy")
        
        engine.register_provider(unhealthy1)
        engine.register_provider(unhealthy2)
        
        with pytest.raises(RuntimeError, match="No healthy providers available"):
            params = AnalyzeParams(symbol_name="test", file_path="/test")
            engine.execute_with_fallback("analyze_symbol", "python", params)
            
    def test_partial_capability_coverage(self):
        """Should handle cases where providers have partial capability coverage"""
        engine = RefactoringEngine()
        
        # Provider that only supports analysis
        analyzer_only = Mock()
        analyzer_only.supports_language.return_value = True
        analyzer_only.get_capabilities.return_value = ["analyze"]
        analyzer_only.is_healthy.return_value = True
        
        engine.register_provider(analyzer_only)
        
        # Should work for supported operations
        analyze_providers = engine.get_providers_with_capability("python", "analyze")
        assert len(analyze_providers) == 1
        
        # Should return empty for unsupported operations
        rename_providers = engine.get_providers_with_capability("python", "rename")
        assert len(rename_providers) == 0