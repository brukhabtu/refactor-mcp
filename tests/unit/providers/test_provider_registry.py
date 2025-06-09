"""Tests for enhanced provider registry functionality"""

import pytest
from unittest.mock import Mock
from typing import List

from refactor_mcp.providers.registry import RefactoringEngine
from refactor_mcp.models.params import AnalyzeParams


class MockProvider:
    """Mock provider for testing"""
    
    def __init__(self, name: str, languages: List[str], capabilities: List[str], priority: int = 1, healthy: bool = True):
        self.name = name
        self._languages = languages
        self._capabilities = capabilities
        self.priority = priority
        self._healthy = healthy
        self.call_count = 0
        
    def supports_language(self, language: str) -> bool:
        return language in self._languages
        
    def get_capabilities(self, language: str) -> List[str]:
        if language in self._languages:
            return self._capabilities
        return []
        
    def get_priority(self) -> int:
        return self.priority
        
    def is_healthy(self) -> bool:
        return self._healthy
        
    def analyze_symbol(self, params: AnalyzeParams):
        self.call_count += 1
        if not self._healthy:
            raise RuntimeError(f"Provider {self.name} is unhealthy")
        return Mock(success=True, provider=self.name)


class TestMultiProviderRegistry:
    """Test multi-provider support and intelligent selection"""
    
    def test_register_multiple_providers_for_same_language(self):
        """Should allow multiple providers for same language"""
        engine = RefactoringEngine()
        
        provider1 = MockProvider("rope", ["python"], ["analyze", "rename"], priority=2)
        provider2 = MockProvider("tree-sitter", ["python"], ["analyze"], priority=1)
        
        engine.register_provider(provider1, priority=provider1.priority)
        engine.register_provider(provider2, priority=provider2.priority)
        
        providers = engine.get_providers("python")
        assert len(providers) == 2
        assert provider1 in providers
        assert provider2 in providers
        
    def test_priority_based_provider_selection(self):
        """Should select highest priority provider for language"""
        engine = RefactoringEngine()
        
        low_priority = MockProvider("low", ["python"], ["analyze"], priority=1)
        high_priority = MockProvider("high", ["python"], ["analyze", "rename"], priority=3)
        medium_priority = MockProvider("medium", ["python"], ["analyze"], priority=2)
        
        engine.register_provider(low_priority, priority=low_priority.priority)
        engine.register_provider(high_priority, priority=high_priority.priority)
        engine.register_provider(medium_priority, priority=medium_priority.priority)
        
        provider = engine.get_best_provider("python")
        assert provider == high_priority
        
    def test_capability_based_provider_filtering(self):
        """Should filter providers by required capabilities"""
        engine = RefactoringEngine()
        
        basic_provider = MockProvider("basic", ["python"], ["analyze"])
        advanced_provider = MockProvider("advanced", ["python"], ["analyze", "rename", "extract"])
        
        engine.register_provider(basic_provider)
        engine.register_provider(advanced_provider)
        
        # Should return only advanced provider for rename capability
        providers = engine.get_providers_with_capability("python", "rename")
        assert len(providers) == 1
        assert providers[0] == advanced_provider
        
        # Should return both for analyze capability
        providers = engine.get_providers_with_capability("python", "analyze")
        assert len(providers) == 2
        
    def test_provider_fallback_mechanism(self):
        """Should fallback to next provider when operation fails"""
        engine = RefactoringEngine()
        
        failing_provider = MockProvider("failing", ["python"], ["analyze"], priority=3, healthy=False)
        working_provider = MockProvider("working", ["python"], ["analyze"], priority=2, healthy=True)
        
        engine.register_provider(failing_provider)
        engine.register_provider(working_provider)
        
        params = AnalyzeParams(symbol_name="test.symbol", file_path="/test")
        result = engine.execute_with_fallback("analyze_symbol", "python", params)
        
        assert result.success is True
        assert result.provider == "working"
        assert failing_provider.call_count == 1  # Should have tried failing provider first
        assert working_provider.call_count == 1  # Should have fallen back to working provider
        
    def test_provider_discovery_and_auto_registration(self):
        """Should discover and auto-register providers from modules"""
        engine = RefactoringEngine()
        
        # Mock the discovery mechanism
        discovered_providers = [
            MockProvider("rope", ["python"], ["analyze", "rename"]),
            MockProvider("tree-sitter", ["python", "javascript"], ["analyze"])
        ]
        
        engine.discover_and_register_providers(discovered_providers)
        
        assert len(engine.get_providers("python")) == 2
        assert len(engine.get_providers("javascript")) == 1
        
    def test_capability_caching_for_performance(self):
        """Should cache provider capabilities for performance"""
        engine = RefactoringEngine()
        
        provider = MockProvider("test", ["python"], ["analyze", "rename"])
        provider.get_capabilities = Mock(return_value=["analyze", "rename"])
        
        engine.register_provider(provider)
        
        # First call should hit the provider
        caps1 = engine.get_cached_capabilities("python", provider)
        assert provider.get_capabilities.call_count == 1
        
        # Second call should use cache
        caps2 = engine.get_cached_capabilities("python", provider)
        assert provider.get_capabilities.call_count == 1  # No additional call
        assert caps1 == caps2
        
    def test_provider_health_checks(self):
        """Should check provider health and exclude unhealthy ones"""
        engine = RefactoringEngine()
        
        healthy_provider = MockProvider("healthy", ["python"], ["analyze"], healthy=True)
        unhealthy_provider = MockProvider("unhealthy", ["python"], ["analyze"], healthy=False)
        
        engine.register_provider(healthy_provider)
        engine.register_provider(unhealthy_provider)
        
        healthy_providers = engine.get_healthy_providers("python")
        assert len(healthy_providers) == 1
        assert healthy_providers[0] == healthy_provider
        
    def test_provider_lifecycle_management(self):
        """Should support provider load/unload lifecycle"""
        engine = RefactoringEngine()
        
        provider = MockProvider("test", ["python"], ["analyze"])
        provider.load = Mock()
        provider.unload = Mock()
        
        engine.register_provider(provider)
        engine.load_provider(provider)
        assert provider.load.called
        
        engine.unload_provider(provider)
        assert provider.unload.called
        assert provider not in engine.get_providers("python")


class TestRegistryIntegration:
    """Test registry integration with existing components"""
    
    def test_backward_compatibility_with_existing_providers(self):
        """Should work with existing provider interface"""
        engine = RefactoringEngine()
        
        # Mock existing rope provider style
        old_provider = Mock()
        old_provider.supports_language.return_value = True
        old_provider.get_capabilities.return_value = ["analyze", "rename"]
        
        engine.register_provider(old_provider)
        
        provider = engine.get_provider("python")  # Old interface
        assert provider == old_provider
        
    def test_integration_with_engine_operations(self):
        """Should integrate seamlessly with engine.py operations"""
        engine = RefactoringEngine()
        
        provider = MockProvider("test", ["python"], ["analyze"])
        engine.register_provider(provider)
        
        # Should be able to execute operations through registry
        params = AnalyzeParams(symbol_name="test.symbol", file_path="/test")
        result = engine.execute_operation("analyze_symbol", "python", params)
        
        assert result.success is True
        assert provider.call_count == 1


class TestRegistryPerformance:
    """Test registry performance characteristics"""
    
    def test_provider_selection_caching(self):
        """Should cache provider selection for performance"""
        engine = RefactoringEngine()
        
        provider = MockProvider("test", ["python"], ["analyze"])
        engine.register_provider(provider)
        
        # Multiple calls should use cached result
        p1 = engine.get_best_provider("python")
        p2 = engine.get_best_provider("python")
        
        assert p1 == p2
        assert p1 == provider
        
    def test_large_provider_registry_performance(self):
        """Should handle large number of providers efficiently"""
        engine = RefactoringEngine()
        
        # Register many providers
        for i in range(100):
            provider = MockProvider(f"provider_{i}", ["python"], ["analyze"], priority=i)
            engine.register_provider(provider, priority=i)
        
        # Should still be fast to find best provider
        best = engine.get_best_provider("python")
        assert best.priority == 99  # Highest priority


class TestRegistryErrorHandling:
    """Test registry error handling scenarios"""
    
    def test_no_providers_for_language(self):
        """Should handle case when no providers support language"""
        engine = RefactoringEngine()
        
        provider = MockProvider("python_only", ["python"], ["analyze"])
        engine.register_provider(provider)
        
        assert engine.get_provider("unsupported") is None
        assert engine.get_providers("unsupported") == []
        
    def test_all_providers_fail_scenario(self):
        """Should handle case when all providers fail"""
        engine = RefactoringEngine()
        
        provider1 = MockProvider("fail1", ["python"], ["analyze"], healthy=False)
        provider2 = MockProvider("fail2", ["python"], ["analyze"], healthy=False)
        
        engine.register_provider(provider1, priority=provider1.priority)
        engine.register_provider(provider2, priority=provider2.priority)
        
        params = AnalyzeParams(symbol_name="test.symbol", file_path="/test")
        
        with pytest.raises(RuntimeError, match="No healthy providers available"):
            engine.execute_with_fallback("analyze_symbol", "python", params)
            
    def test_invalid_capability_requests(self):
        """Should handle invalid capability requests gracefully"""
        engine = RefactoringEngine()
        
        provider = MockProvider("test", ["python"], ["analyze"])
        engine.register_provider(provider)
        
        # Should return empty list for unsupported capability
        providers = engine.get_providers_with_capability("python", "unsupported_op")
        assert providers == []