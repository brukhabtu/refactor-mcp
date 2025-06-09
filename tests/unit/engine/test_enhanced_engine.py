"""Tests for enhanced RefactoringEngine with intelligent provider selection and fallback."""

import pytest
from typing import List, Dict, Any
import time

from refactor_mcp.engine import RefactoringEngine
from refactor_mcp.models.errors import UnsupportedLanguageError, ProviderError
from refactor_mcp.models.params import AnalyzeParams, FindParams, ShowParams, RenameParams, ExtractParams
from refactor_mcp.models.responses import AnalysisResult, FindResult, ShowResult, RenameResult, ExtractResult
from refactor_mcp.providers.base import RefactoringProvider


class EnhancedMockProvider(RefactoringProvider):
    """Enhanced mock provider with priority, health tracking, and capabilities."""
    
    def __init__(
        self, 
        name: str,
        supported_languages: List[str] = None, 
        capabilities: Dict[str, List[str]] = None,
        priority: int = 100,
        failure_rate: float = 0.0,
        response_time: float = 0.1
    ):
        self.name = name
        self.supported_languages = supported_languages or ['python']
        self._capabilities = capabilities or {}
        self.priority = priority
        self.failure_rate = failure_rate
        self.response_time = response_time
        self.call_count = 0
        self.failure_count = 0
        self.call_history = []
        self.health_score = 1.0  # Start with perfect health
    
    def supports_language(self, language: str) -> bool:
        return language in self.supported_languages
    
    def get_capabilities(self, language: str) -> List[str]:
        if language in self.supported_languages:
            return self._capabilities.get(language, ["analyze_symbol", "find_symbols", "show_function", "rename_symbol", "extract_element"])
        return []
    
    def get_priority(self) -> int:
        """Return provider priority (lower = higher priority)."""
        return self.priority
    
    def get_health_score(self) -> float:
        """Return current health score (0.0 to 1.0)."""
        return self.health_score
    
    def _simulate_call(self, operation: str, params: Any):
        """Simulate a provider call with potential failure and delay."""
        self.call_count += 1
        self.call_history.append((operation, params, time.time()))
        
        # Simulate response time
        time.sleep(self.response_time)
        
        # Simulate failure - deterministic based on call count and failure rate
        if self.failure_rate >= 1.0:  # Always fail
            self.failure_count += 1
            self.health_score = max(0.0, 1.0 - (self.failure_count / self.call_count))
            raise Exception(f"{self.name} simulated failure")
        elif self.failure_rate > 0 and (self.call_count <= self.failure_rate * 10):
            # Fail for first few calls based on failure rate
            self.failure_count += 1
            self.health_score = max(0.0, 1.0 - (self.failure_count / self.call_count))
            raise Exception(f"{self.name} simulated failure")
        
        return True
    
    def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
        self._simulate_call('analyze_symbol', params)
        
        from refactor_mcp.models.responses import SymbolInfo
        
        symbol_info = SymbolInfo(
            name=params.symbol_name,
            qualified_name=params.symbol_name,
            type="function",
            definition_location="test.py:10",
            scope="module"
        )
        
        return AnalysisResult(
            success=True,
            symbol_info=symbol_info,
            references=[],
            reference_count=0,
            refactoring_suggestions=[]
        )
    
    def find_symbols(self, params: FindParams) -> FindResult:
        self._simulate_call('find_symbols', params)
        
        return FindResult(
            success=True,
            pattern=params.pattern,
            matches=[],
            total_count=0
        )
    
    def show_function(self, params: ShowParams) -> ShowResult:
        self._simulate_call('show_function', params)
        
        return ShowResult(
            success=True,
            function_name=params.function_name,
            extractable_elements=[]
        )
    
    def rename_symbol(self, params: RenameParams) -> RenameResult:
        self._simulate_call('rename_symbol', params)
        
        return RenameResult(
            success=True,
            old_name=params.symbol_name,
            new_name=params.new_name,
            qualified_name=params.symbol_name,
            files_modified=["test.py"],
            references_updated=1
        )
    
    def extract_element(self, params: ExtractParams) -> ExtractResult:
        self._simulate_call('extract_element', params)
        
        return ExtractResult(
            success=True,
            source=params.source,
            new_function_name=params.new_name,
            extracted_code="def extracted_function(): pass",
            parameters=[],
            files_modified=["test.py"]
        )


@pytest.fixture
def enhanced_engine():
    """Create an enhanced RefactoringEngine for testing."""
    return RefactoringEngine()


@pytest.fixture
def high_priority_provider():
    """Create a high-priority provider."""
    return EnhancedMockProvider(
        name="HighPriorityProvider",
        priority=10,
        capabilities={"python": ["analyze_symbol", "rename_symbol"]}
    )


@pytest.fixture
def low_priority_provider():
    """Create a low-priority provider."""
    return EnhancedMockProvider(
        name="LowPriorityProvider", 
        priority=100,
        capabilities={"python": ["analyze_symbol", "find_symbols", "extract_element"]}
    )


@pytest.fixture
def unreliable_provider():
    """Create an unreliable provider that fails frequently."""
    return EnhancedMockProvider(
        name="UnreliableProvider",
        priority=5,  # High priority but unreliable
        failure_rate=0.8,  # 80% failure rate
        capabilities={"python": ["analyze_symbol", "rename_symbol"]}
    )


@pytest.fixture
def slow_provider():
    """Create a slow but reliable provider."""
    return EnhancedMockProvider(
        name="SlowProvider",
        priority=20,
        response_time=0.5,  # 500ms response time
        capabilities={"python": ["analyze_symbol", "rename_symbol", "extract_element"]}
    )


class TestIntelligentProviderSelection:
    """Test intelligent provider selection based on capabilities and priority."""
    
    def test_selects_provider_by_priority(self, enhanced_engine, high_priority_provider, low_priority_provider):
        """Should select provider with higher priority (lower number)."""
        enhanced_engine.register_provider(low_priority_provider)
        enhanced_engine.register_provider(high_priority_provider)
        
        params = AnalyzeParams(symbol_name="test_function")
        result = enhanced_engine.analyze_symbol_with_fallback(params)
        
        assert result.success is True
        assert high_priority_provider.call_count == 1
        assert low_priority_provider.call_count == 0
    
    def test_selects_provider_by_capability(self, enhanced_engine, high_priority_provider, low_priority_provider):
        """Should select provider that supports the requested operation."""
        # High priority provider doesn't support find_symbols
        high_priority_provider._capabilities = {"python": ["analyze_symbol", "rename_symbol"]}
        
        enhanced_engine.register_provider(high_priority_provider)
        enhanced_engine.register_provider(low_priority_provider)
        
        params = FindParams(pattern="test")
        result = enhanced_engine.find_symbols_with_fallback(params)
        
        assert result.success is True
        assert high_priority_provider.call_count == 0  # Doesn't support find_symbols
        assert low_priority_provider.call_count == 1   # Has find_symbols capability
    
    def test_no_provider_supports_operation(self, enhanced_engine):
        """Should raise error when no provider supports the operation."""
        # Provider with no capabilities
        provider = EnhancedMockProvider(
            name="NoCapProvider",
            capabilities={"python": []}  # No capabilities
        )
        enhanced_engine.register_provider(provider)
        
        params = AnalyzeParams(symbol_name="test_function")
        
        with pytest.raises(UnsupportedLanguageError):
            enhanced_engine.analyze_symbol_with_fallback(params)


class TestFallbackMechanisms:
    """Test fallback mechanisms when primary provider fails."""
    
    def test_fallback_to_next_provider(self, enhanced_engine, unreliable_provider, low_priority_provider):
        """Should fallback to next provider when primary fails."""
        enhanced_engine.register_provider(unreliable_provider)
        enhanced_engine.register_provider(low_priority_provider)
        
        params = AnalyzeParams(symbol_name="test_function")
        result = enhanced_engine.analyze_symbol_with_fallback(params)
        
        assert result.success is True
        assert unreliable_provider.call_count >= 1  # Primary tried first
        assert low_priority_provider.call_count == 1  # Fallback succeeded
    
    def test_fallback_exhausts_all_providers(self, enhanced_engine):
        """Should try all providers before giving up."""
        unreliable1 = EnhancedMockProvider(name="Unreliable1", priority=10, failure_rate=1.0)
        unreliable2 = EnhancedMockProvider(name="Unreliable2", priority=20, failure_rate=1.0)
        
        enhanced_engine.register_provider(unreliable1)
        enhanced_engine.register_provider(unreliable2)
        
        params = AnalyzeParams(symbol_name="test_function")
        
        with pytest.raises(ProviderError):
            enhanced_engine.analyze_symbol_with_fallback(params)
        
        assert unreliable1.call_count == 1
        assert unreliable2.call_count == 1
    
    def test_fallback_respects_capabilities(self, enhanced_engine):
        """Should only fallback to providers that support the operation."""
        # Primary provider supports analyze but will fail
        primary = EnhancedMockProvider(
            name="Primary", 
            priority=10, 
            failure_rate=1.0,
            capabilities={"python": ["analyze_symbol"]}
        )
        
        # Fallback provider doesn't support analyze  
        fallback = EnhancedMockProvider(
            name="Fallback",
            priority=20,
            capabilities={"python": ["find_symbols"]}  # No analyze_symbol
        )
        
        enhanced_engine.register_provider(primary)
        enhanced_engine.register_provider(fallback)
        
        params = AnalyzeParams(symbol_name="test_function")
        
        with pytest.raises(ProviderError):
            enhanced_engine.analyze_symbol_with_fallback(params)
        
        assert primary.call_count == 1
        assert fallback.call_count == 0  # Never tried due to lack of capability


class TestProviderHealthMonitoring:
    """Test provider health monitoring and recovery."""
    
    def test_tracks_provider_health(self, enhanced_engine):
        """Should track provider health based on success/failure rates."""
        # Create a provider that will fail
        failing_provider = EnhancedMockProvider(
            name="FailingProvider",
            failure_rate=1.0  # Always fails
        )
        enhanced_engine.register_provider(failing_provider)
        
        # Initial health should be 1.0
        metrics = enhanced_engine.get_provider_metrics("FailingProvider")
        assert metrics["health_score"] == 1.0
        
        # After failures, health should decrease
        try:
            params = AnalyzeParams(symbol_name="test_function")
            enhanced_engine.analyze_symbol_with_fallback(params)
        except Exception:
            pass
        
        # Health should be reduced after failures
        metrics = enhanced_engine.get_provider_metrics("FailingProvider")
        assert metrics["health_score"] < 1.0
    
    def test_prefers_healthy_providers(self, enhanced_engine):
        """Should prefer providers with better health scores."""
        # Create two providers with same priority but different health
        provider1 = EnhancedMockProvider(name="Healthy", priority=50, failure_rate=0.0)
        provider2 = EnhancedMockProvider(name="Unhealthy", priority=50, failure_rate=1.0)
        
        # Degrade provider2's health
        provider2.health_score = 0.3
        
        enhanced_engine.register_provider(provider1)
        enhanced_engine.register_provider(provider2)
        
        params = AnalyzeParams(symbol_name="test_function")
        result = enhanced_engine.analyze_symbol_with_fallback(params)
        
        assert result.success is True
        assert provider1.call_count == 1  # Healthy provider used
        assert provider2.call_count == 0  # Unhealthy provider skipped


class TestLanguageDetectionAndRouting:
    """Test enhanced language detection and provider routing."""
    
    def test_routes_to_language_specific_provider(self, enhanced_engine):
        """Should route operations to providers that support the detected language."""
        python_provider = EnhancedMockProvider(
            name="PythonProvider",
            supported_languages=["python"],
            priority=10
        )
        js_provider = EnhancedMockProvider(
            name="JSProvider", 
            supported_languages=["javascript"],
            priority=10
        )
        
        enhanced_engine.register_provider(python_provider)
        enhanced_engine.register_provider(js_provider)
        
        # Should use Python provider for Python files
        params = AnalyzeParams(symbol_name="test_function")
        result = enhanced_engine.analyze_symbol_with_language_detection(params, "test.py")
        
        assert result.success is True
        assert python_provider.call_count == 1
        assert js_provider.call_count == 0
    
    def test_fallback_to_universal_provider(self, enhanced_engine):
        """Should fallback to universal providers when language-specific ones fail."""
        python_provider = EnhancedMockProvider(
            name="PythonProvider",
            supported_languages=["python"],
            priority=10,
            failure_rate=1.0  # Always fails
        )
        universal_provider = EnhancedMockProvider(
            name="UniversalProvider",
            supported_languages=["python", "javascript", "typescript"],
            priority=50  # Lower priority
        )
        
        enhanced_engine.register_provider(python_provider)
        enhanced_engine.register_provider(universal_provider)
        
        params = AnalyzeParams(symbol_name="test_function")
        result = enhanced_engine.analyze_symbol_with_language_detection(params, "test.py")
        
        assert result.success is True
        assert python_provider.call_count == 1  # Tried first but failed
        assert universal_provider.call_count == 1  # Fallback succeeded


class TestPerformanceAndMetrics:
    """Test performance monitoring and operation metrics."""
    
    def test_tracks_operation_timing(self, enhanced_engine, slow_provider):
        """Should track operation timing and performance metrics."""
        enhanced_engine.register_provider(slow_provider)
        
        params = AnalyzeParams(symbol_name="test_function")
        start_time = time.time()
        result = enhanced_engine.analyze_symbol_with_fallback(params)
        end_time = time.time()
        
        assert result.success is True
        # Should account for provider response time
        assert (end_time - start_time) >= slow_provider.response_time
    
    def test_collects_provider_metrics(self, enhanced_engine, high_priority_provider):
        """Should collect and expose provider performance metrics."""
        enhanced_engine.register_provider(high_priority_provider)
        
        # Perform several operations
        for i in range(5):
            params = AnalyzeParams(symbol_name=f"test_function_{i}")
            enhanced_engine.analyze_symbol_with_fallback(params)
        
        metrics = enhanced_engine.get_provider_metrics(high_priority_provider.name)
        
        assert metrics["call_count"] == 5
        assert metrics["failure_count"] == 0
        assert metrics["health_score"] == 1.0
        assert "avg_response_time" in metrics


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""
    
    def test_graceful_degradation_on_partial_failure(self, enhanced_engine):
        """Should gracefully degrade when some providers fail."""
        working_provider = EnhancedMockProvider(
            name="WorkingProvider",
            capabilities={"python": ["analyze_symbol", "find_symbols"]}
        )
        broken_provider = EnhancedMockProvider(
            name="BrokenProvider",
            failure_rate=1.0,
            capabilities={"python": ["rename_symbol", "extract_element"]}
        )
        
        enhanced_engine.register_provider(working_provider)
        enhanced_engine.register_provider(broken_provider)
        
        # Should work for supported operations
        params = AnalyzeParams(symbol_name="test_function")
        result = enhanced_engine.analyze_symbol_with_fallback(params)
        assert result.success is True
        
        # Should fail gracefully for unsupported operations
        rename_params = RenameParams(symbol_name="old_name", new_name="new_name")
        with pytest.raises(ProviderError):
            enhanced_engine.rename_symbol_with_fallback(rename_params)
    
    def test_provider_isolation(self, enhanced_engine):
        """Should isolate provider failures and not affect other providers."""
        good_provider = EnhancedMockProvider(name="GoodProvider", priority=20)
        bad_provider = EnhancedMockProvider(name="BadProvider", priority=10, failure_rate=1.0)
        
        enhanced_engine.register_provider(bad_provider)
        enhanced_engine.register_provider(good_provider)
        
        # Even though bad provider fails, good provider should still work
        params = AnalyzeParams(symbol_name="test_function")
        result = enhanced_engine.analyze_symbol_with_fallback(params)
        
        assert result.success is True
        assert bad_provider.call_count == 1  # Failed
        assert good_provider.call_count == 1  # Succeeded