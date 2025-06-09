"""
Comprehensive integration tests for the provider system.

This module tests the complete provider ecosystem including multi-provider
scenarios, system integration, and end-to-end workflows.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from refactor_mcp.providers.base import RefactoringProvider
from refactor_mcp.providers.registry import RefactoringEngine, engine
from refactor_mcp.models.params import AnalyzeParams, RenameParams, ExtractParams, FindParams, ShowParams
from refactor_mcp.models.responses import AnalysisResult, RenameResult, ExtractResult, FindResult, ShowResult, ErrorResponse
from refactor_mcp.models import SymbolInfo, ElementInfo

from tests.mocks.providers import MockRopeProvider, MockTreeSitterProvider, FailingProvider, ConfigurableProvider
from tests.mocks.provider_testing_framework import (
    ProviderTestFramework, ProviderTestBuilder, ProviderComplianceValidator,
    ProviderPerformanceBenchmark, MockProviderFactory, TestDataGenerator
)


class TestMultiProviderIntegration:
    """Test integration scenarios with multiple providers."""
    
    def setup_method(self):
        """Set up test environment with multiple providers."""
        self.test_engine = RefactoringEngine()
        self.rope_provider = MockRopeProvider()
        self.tree_sitter_provider = MockTreeSitterProvider()
        self.failing_provider = FailingProvider()
        
        self.test_engine.register_provider(self.rope_provider)
        self.test_engine.register_provider(self.tree_sitter_provider)
    
    def test_provider_selection_by_language(self):
        """Test engine selects appropriate provider for language."""
        # Test Python - should select first provider (Rope)
        python_provider = self.test_engine.get_provider("python")
        assert python_provider == self.rope_provider
        
        # Test JavaScript - should select TreeSitter
        js_provider = self.test_engine.get_provider("javascript")
        assert js_provider == self.tree_sitter_provider
        
        # Test unsupported language
        unsupported_provider = self.test_engine.get_provider("cobol")
        assert unsupported_provider is None
    
    def test_provider_fallback_on_failure(self):
        """Test system handles provider failures gracefully."""
        # Register failing provider first
        fallback_engine = RefactoringEngine()
        fallback_engine.register_provider(self.failing_provider)
        fallback_engine.register_provider(self.rope_provider)
        
        # Should get failing provider first
        provider = fallback_engine.get_provider("python")
        assert provider == self.failing_provider
        
        # In real implementation, we'd need fallback logic
        # For now, test that we can detect failures
        result = provider.analyze_symbol(AnalyzeParams(symbol_name="test"))
        assert isinstance(result, ErrorResponse)
        assert not result.success
    
    def test_cross_provider_consistency(self):
        """Test consistency across different providers."""
        params = AnalyzeParams(symbol_name="test_symbol")
        
        # Both providers should handle the same operation
        rope_result = self.rope_provider.analyze_symbol(params)
        tree_sitter_result = self.tree_sitter_provider.analyze_symbol(params)
        
        # Both should succeed (mock providers)
        assert rope_result.success
        assert tree_sitter_result.success
        
        # Both should return proper result types
        assert isinstance(rope_result, AnalysisResult)
        assert isinstance(tree_sitter_result, AnalysisResult)
    
    def test_provider_capabilities_aggregation(self):
        """Test aggregating capabilities across providers."""
        # Get all supported languages
        languages = self.test_engine.get_supported_languages()
        
        # Should include languages from all providers
        # Note: This depends on implementation of get_supported_languages
        # For now, test basic functionality
        assert isinstance(languages, list)
    
    def test_provider_performance_comparison(self):
        """Test comparing performance across providers."""
        framework = ProviderTestFramework()
        framework.register_provider(self.rope_provider)
        framework.register_provider(self.tree_sitter_provider)
        
        # Create benchmark
        benchmark = ProviderPerformanceBenchmark()
        benchmark.add_provider(self.rope_provider)
        benchmark.add_provider(self.tree_sitter_provider)
        
        # Run comparison
        comparison = benchmark.run_comparison(["analyze_symbol", "rename_symbol"])
        
        assert len(comparison.provider_results) == 2
        assert "mock_rope" in comparison.provider_results
        assert "mock_tree_sitter" in comparison.provider_results
        assert len(comparison.performance_ranking) == 2


class TestProviderTestingFrameworkIntegration:
    """Test the provider testing framework with real provider scenarios."""
    
    def setup_method(self):
        """Set up testing framework."""
        self.framework = ProviderTestFramework()
        self.mock_provider = MockRopeProvider()
        self.framework.register_provider(self.mock_provider)
    
    def test_complete_testing_workflow(self):
        """Test end-to-end testing workflow."""
        # 1. Generate test data
        generator = TestDataGenerator()
        test_data = generator.generate_complete_test_suite()
        
        # 2. Build test cases
        builder = ProviderTestBuilder()
        test_cases = (builder
                     .add_analyze_test("get_user_info")
                     .add_rename_test("get_user_info", "get_user_data")
                     .add_extract_test("process_users.lambda_2", "is_valid_user")
                     .add_validation_scenario("symbol_not_found")
                     .build())
        
        # 3. Execute tests
        results = self.framework.execute_test_batch(test_cases, "mock_rope")
        
        # 4. Validate results
        assert len(results) == 4
        
        # First three should succeed (valid symbols in mock provider)
        assert results[0].success  # analyze existing symbol
        assert results[1].success  # rename existing symbol
        assert results[2].success  # extract existing element
        
        # Last should fail (invalid symbol)
        assert not results[3].success  # symbol not found
    
    def test_provider_compliance_validation(self):
        """Test provider compliance validation."""
        validator = ProviderComplianceValidator()
        
        # Test interface compliance
        compliance_result = validator.validate_interface(self.mock_provider)
        assert compliance_result.is_compliant
        assert len(compliance_result.missing_methods) == 0
        
        # Test error handling
        error_result = validator.validate_error_handling(self.mock_provider)
        assert error_result.handles_errors_correctly
        assert error_result.error_scenarios_tested > 0
    
    def test_configurable_provider_scenarios(self):
        """Test configurable provider for specific scenarios."""
        configurable = ConfigurableProvider("test_configurable")
        
        # Configure specific responses
        configurable.configure_analyze_response(
            "valid_symbol",
            AnalysisResult(
                success=True,
                symbol_info=SymbolInfo(name="valid_symbol", qualified_name="test.valid_symbol", type="function"),
                references=["test.py:1"],
                reference_count=1
            )
        )
        
        configurable.configure_analyze_response(
            "invalid_symbol",
            ErrorResponse(
                success=False,
                error_type="symbol_not_found",
                error_message="Symbol not found",
                suggestions=[]
            )
        )
        
        # Test configured responses
        valid_result = configurable.analyze_symbol(AnalyzeParams(symbol_name="valid_symbol"))
        assert valid_result.success
        
        invalid_result = configurable.analyze_symbol(AnalyzeParams(symbol_name="invalid_symbol"))
        assert not invalid_result.success
        assert invalid_result.error_type == "symbol_not_found"
    
    def test_performance_benchmarking(self):
        """Test performance benchmarking functionality."""
        benchmark = ProviderPerformanceBenchmark()
        benchmark.add_provider(self.mock_provider)
        
        # Test individual operation timing
        result = benchmark.time_operation(
            self.mock_provider,
            "analyze_symbol",
            AnalyzeParams(symbol_name="get_user_info")
        )
        
        assert result.provider_name == "mock_rope"
        assert result.operation == "analyze_symbol"
        assert result.execution_time >= 0
        assert result.success
        
        # Test scalability
        scalability_result = benchmark.test_scalability(
            self.mock_provider,
            "find_symbols",
            [1, 10, 100]
        )
        
        assert "scale_results" in scalability_result
        assert "scalability_score" in scalability_result
        assert len(scalability_result["scale_results"]) == 3


class TestProviderErrorHandling:
    """Test comprehensive error handling across the provider system."""
    
    def setup_method(self):
        """Set up error testing environment."""
        self.framework = ProviderTestFramework()
        self.failing_provider = FailingProvider("timeout_error")
        self.mock_provider = MockRopeProvider()
        
        self.framework.register_provider(self.failing_provider)
        self.framework.register_provider(self.mock_provider)
    
    def test_provider_failure_scenarios(self):
        """Test various provider failure scenarios."""
        # Test timeout failures
        timeout_provider = FailingProvider("timeout")
        
        # This should not raise an exception, but return error response
        result = timeout_provider.analyze_symbol(AnalyzeParams(symbol_name="test"))
        assert isinstance(result, ErrorResponse)
        assert not result.success
        
        # Test error responses
        error_provider = FailingProvider("error")
        result = error_provider.analyze_symbol(AnalyzeParams(symbol_name="test"))
        assert isinstance(result, ErrorResponse)
        assert not result.success
        assert result.error_type == "provider_error"
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs across providers."""
        test_cases = [
            AnalyzeParams(symbol_name=""),  # Empty symbol name
            AnalyzeParams(symbol_name="a" * 1000),  # Very long symbol name
            RenameParams(symbol_name="valid", new_name=""),  # Empty new name
            ExtractParams(source="invalid", new_name="test"),  # Invalid source format
        ]
        
        for params in test_cases:
            if isinstance(params, AnalyzeParams):
                result = self.mock_provider.analyze_symbol(params)
            elif isinstance(params, RenameParams):
                result = self.mock_provider.rename_symbol(params)
            elif isinstance(params, ExtractParams):
                result = self.mock_provider.extract_element(params)
            
            # Provider should handle gracefully, not crash
            assert result is not None
            assert hasattr(result, 'success')
    
    def test_edge_case_scenarios(self):
        """Test edge cases in provider operations."""
        # Test symbols with special characters
        special_symbol = AnalyzeParams(symbol_name="special_symbol_!@#$%")
        result = self.mock_provider.analyze_symbol(special_symbol)
        assert result is not None
        
        # Test very complex qualified names
        complex_extract = ExtractParams(
            source="deeply.nested.module.function.inner.lambda_1",
            new_name="extracted_function"
        )
        result = self.mock_provider.extract_element(complex_extract)
        assert result is not None
        
        # Test pattern matching edge cases
        pattern_tests = [
            FindParams(pattern=""),  # Empty pattern
            FindParams(pattern="*"),  # Match all
            FindParams(pattern="very_specific_pattern_that_probably_doesnt_exist"),
        ]
        
        for pattern_param in pattern_tests:
            result = self.mock_provider.find_symbols(pattern_param)
            assert result is not None
            assert hasattr(result, 'success')


class TestProviderFactoryIntegration:
    """Test provider factory integration with the testing framework."""
    
    def setup_method(self):
        """Set up provider factory tests."""
        self.factory = MockProviderFactory()
        self.framework = ProviderTestFramework()
    
    def test_factory_provider_creation(self):
        """Test creating providers through factory."""
        # Create basic provider
        basic_provider = self.factory.create_basic_provider(
            "test_basic",
            languages=["python", "javascript"],
            capabilities=["analyze", "rename"]
        )
        
        assert basic_provider.name == "test_basic"
        assert basic_provider.supports_language("python")
        assert basic_provider.supports_language("javascript")
        
        # Test that provider works with framework
        self.framework.register_provider(basic_provider)
        
        test_case = ProviderTestBuilder().add_analyze_test("test_symbol").build()[0]
        result = self.framework.execute_test_case(test_case, "test_basic")
        
        assert result.success
    
    def test_factory_failing_provider_creation(self):
        """Test creating failing providers for error testing."""
        failing_provider = self.factory.create_failing_provider(
            "test_failing",
            failure_mode="timeout",
            failure_operations=["analyze_symbol"]
        )
        
        # Register and test
        self.framework.register_provider(failing_provider)
        
        test_case = ProviderTestBuilder().add_analyze_test("test_symbol", expected_success=False).build()[0]
        result = self.framework.execute_test_case(test_case, "test_failing")
        
        # Should fail as expected
        assert not result.success
        assert result.error is not None
    
    def test_factory_latency_simulation(self):
        """Test latency simulation in providers."""
        slow_provider = self.factory.create_slow_provider("test_slow", latency_ms=100)
        fast_provider = self.factory.create_fast_provider("test_fast")
        
        benchmark = ProviderPerformanceBenchmark()
        benchmark.add_provider(slow_provider)
        benchmark.add_provider(fast_provider)
        
        comparison = benchmark.run_comparison(["analyze_symbol"])
        
        # Fast provider should be faster
        assert comparison.fastest_provider == "test_fast"
        assert comparison.slowest_provider == "test_slow"
        
        # Slow provider should take at least 100ms
        slow_results = comparison.provider_results["test_slow"]
        assert any(r.execution_time >= 0.1 for r in slow_results)


class TestProviderDataGeneration:
    """Test test data generation for provider testing."""
    
    def setup_method(self):
        """Set up data generation tests."""
        self.generator = TestDataGenerator()
    
    def test_symbol_generation(self):
        """Test generating symbol test data."""
        symbols = self.generator.generate_symbols(
            count=20,
            types=["function", "class", "variable"],
            complexity_levels=["simple", "complex"]
        )
        
        assert len(symbols) == 20
        
        # Check distribution of types
        types = [s.type for s in symbols]
        assert "function" in types
        assert "class" in types
        assert "variable" in types
        
        # Check complexity distribution
        scopes = [s.scope for s in symbols]
        assert "global" in scopes  # simple complexity
        assert "class" in scopes   # complex complexity
    
    def test_code_pattern_generation(self):
        """Test generating code patterns."""
        patterns = self.generator.generate_code_patterns(
            pattern_types=["nested_functions", "lambdas", "complex_expressions"],
            languages=["python"]
        )
        
        assert len(patterns) == 3
        
        # Each pattern should have code and extractable elements
        for pattern in patterns:
            assert "code" in pattern
            assert "extractable_elements" in pattern
            assert len(pattern["extractable_elements"]) > 0
    
    def test_edge_case_generation(self):
        """Test generating edge case scenarios."""
        edge_cases = self.generator.generate_edge_cases(
            categories=["empty_input", "invalid_syntax", "boundary_conditions"]
        )
        
        assert len(edge_cases) == 3
        
        # Each edge case should have scenario and expected behavior
        for edge_case in edge_cases:
            assert "scenario" in edge_case
            assert "expected_behavior" in edge_case
            assert "params" in edge_case
    
    def test_complete_test_suite_generation(self):
        """Test generating complete test suite."""
        test_suite = self.generator.generate_complete_test_suite()
        
        assert "symbols" in test_suite
        assert "code_patterns" in test_suite
        assert "edge_cases" in test_suite
        
        assert len(test_suite["symbols"]) > 0
        assert len(test_suite["code_patterns"]) > 0
        assert len(test_suite["edge_cases"]) > 0


class TestProviderReporting:
    """Test provider test reporting functionality."""
    
    def setup_method(self):
        """Set up reporting tests."""
        from tests.mocks.provider_testing_framework import ProviderTestReporter, ProviderTestResult
        
        self.reporter = ProviderTestReporter()
        
        # Create mock results
        self.mock_results = [
            ProviderTestResult(
                success=True,
                provider_name="provider1",
                test_case_name="test1",
                operation="analyze_symbol",
                execution_time_ms=50.0
            ),
            ProviderTestResult(
                success=False,
                provider_name="provider1",
                test_case_name="test2",
                operation="rename_symbol",
                execution_time_ms=75.0,
                validation_errors=["Missing field"]
            ),
            ProviderTestResult(
                success=True,
                provider_name="provider2",
                test_case_name="test1",
                operation="analyze_symbol",
                execution_time_ms=30.0
            )
        ]
    
    def test_result_aggregation(self):
        """Test aggregating test results."""
        summary = self.reporter.aggregate_results(self.mock_results)
        
        assert summary["total_tests"] == 3
        assert summary["passed_tests"] == 2
        assert summary["failed_tests"] == 1
        assert summary["success_rate"] == 2/3
        
        # Check provider summaries
        assert "provider1" in summary["provider_summaries"]
        assert "provider2" in summary["provider_summaries"]
        
        provider1_summary = summary["provider_summaries"]["provider1"]
        assert provider1_summary["total"] == 2
        assert provider1_summary["passed"] == 1
        assert provider1_summary["failed"] == 1
    
    def test_html_report_generation(self):
        """Test HTML report generation."""
        html_report = self.reporter.generate_html_report(self.mock_results)
        
        assert isinstance(html_report, str)
        assert "<html>" in html_report
        assert "Provider Test Report" in html_report
        assert "provider1" in html_report
        assert "provider2" in html_report
    
    def test_json_report_generation(self):
        """Test JSON report generation."""
        json_report = self.reporter.generate_json_report(self.mock_results)
        
        assert isinstance(json_report, str)
        
        import json
        parsed_report = json.loads(json_report)
        
        assert "timestamp" in parsed_report
        assert "summary" in parsed_report
        assert "detailed_results" in parsed_report
        
        assert len(parsed_report["detailed_results"]) == 3


class TestRealWorldIntegrationScenarios:
    """Test real-world integration scenarios."""
    
    def setup_method(self):
        """Set up real-world testing scenarios."""
        self.framework = ProviderTestFramework()
        self.rope_provider = MockRopeProvider()
        self.framework.register_provider(self.rope_provider)
    
    def test_large_codebase_simulation(self):
        """Test provider performance with large codebase simulation."""
        # Generate large number of symbols
        generator = TestDataGenerator()
        symbols = generator.generate_symbols(count=1000, types=["function", "class", "variable"])
        
        # Create test cases for subset of symbols
        builder = ProviderTestBuilder()
        for symbol in symbols[:10]:  # Test first 10
            builder.add_analyze_test(symbol.name)
        
        test_cases = builder.build()
        results = self.framework.execute_test_batch(test_cases, "mock_rope")
        
        # All should complete successfully
        assert len(results) == 10
        assert all(r.success for r in results)
        
        # Check performance
        avg_time = sum(r.execution_time_ms for r in results) / len(results)
        assert avg_time < 1000  # Should be under 1 second per operation
    
    def test_concurrent_provider_operations(self):
        """Test concurrent operations (simulated)."""
        import threading
        import time
        
        results = []
        errors = []
        
        def run_test():
            try:
                result = self.rope_provider.analyze_symbol(AnalyzeParams(symbol_name="get_user_info"))
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=run_test)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All should complete successfully
        assert len(results) == 5
        assert len(errors) == 0
        assert all(r.success for r in results)
    
    def test_provider_stress_testing(self):
        """Test provider under stress conditions."""
        # Rapid-fire requests
        start_time = time.time()
        
        for i in range(100):
            result = self.rope_provider.analyze_symbol(AnalyzeParams(symbol_name=f"symbol_{i}"))
            
            # Should handle gracefully
            assert result is not None
            assert hasattr(result, 'success')
        
        total_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert total_time < 10.0  # 10 seconds for 100 operations
    
    def test_memory_usage_monitoring(self):
        """Test memory usage during provider operations."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        # Perform many operations
        for i in range(50):
            result = self.rope_provider.analyze_symbol(AnalyzeParams(symbol_name=f"symbol_{i}"))
            
            # Occasionally force garbage collection
            if i % 10 == 0:
                gc.collect()
        
        # Should not have significant memory leaks
        # (This is a basic test - real implementation would need more sophisticated monitoring)
        gc.collect()
        
        # Test passes if we get here without memory errors