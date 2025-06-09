"""
Performance benchmarks for provider selection and operations.

This module provides comprehensive performance testing for the provider system,
including benchmarking, scalability testing, and performance regression detection.
"""

import time
import statistics
import pytest
from typing import List, Dict, Any
from dataclasses import dataclass

from refactor_mcp.models.params import AnalyzeParams, RenameParams, ExtractParams, FindParams, ShowParams
from refactor_mcp.providers.base import RefactoringProvider

from tests.mocks.providers import MockRopeProvider, MockTreeSitterProvider
from tests.mocks.provider_testing_framework import (
    MockProviderFactory
)


@dataclass
class PerformanceMetrics:
    """Performance metrics for benchmark results."""
    operation: str
    provider_name: str
    min_time: float
    max_time: float
    avg_time: float
    median_time: float
    std_dev: float
    throughput: float  # operations per second
    memory_usage_mb: float
    success_rate: float


@dataclass
class ScalabilityMetrics:
    """Scalability metrics for load testing."""
    scale_factors: List[int]
    execution_times: List[float]
    memory_usage: List[float]
    throughput_degradation: float
    scalability_score: float


class ProviderPerformanceSuite:
    """Comprehensive performance testing suite for providers."""
    
    def __init__(self):
        self.providers: Dict[str, RefactoringProvider] = {}
        self.baseline_metrics: Dict[str, PerformanceMetrics] = {}
        self.benchmark_results: List[PerformanceMetrics] = []
    
    def register_provider(self, provider: RefactoringProvider):
        """Register a provider for performance testing."""
        self.providers[provider.name] = provider
    
    def benchmark_operation(self, provider_name: str, operation: str, params: Any, iterations: int = 100) -> PerformanceMetrics:
        """Benchmark a specific operation for a provider."""
        provider = self.providers[provider_name]
        operation_method = getattr(provider, operation)
        
        execution_times = []
        memory_usage_samples = []
        successful_operations = 0
        
        for _ in range(iterations):
            # Measure memory before operation
            start_memory = self._get_memory_usage()
            
            # Time the operation
            start_time = time.perf_counter()
            
            try:
                result = operation_method(params)
                end_time = time.perf_counter()
                
                if hasattr(result, 'success') and result.success:
                    successful_operations += 1
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                # Measure memory after operation
                end_memory = self._get_memory_usage()
                memory_usage_samples.append(end_memory - start_memory)
                
            except Exception:
                # Operation failed - record as failure
                execution_times.append(float('inf'))
                memory_usage_samples.append(0.0)
        
        # Calculate statistics
        valid_times = [t for t in execution_times if t != float('inf')]
        
        if not valid_times:
            # All operations failed
            return PerformanceMetrics(
                operation=operation,
                provider_name=provider_name,
                min_time=float('inf'),
                max_time=float('inf'),
                avg_time=float('inf'),
                median_time=float('inf'),
                std_dev=float('inf'),
                throughput=0.0,
                memory_usage_mb=0.0,
                success_rate=0.0
            )
        
        min_time = min(valid_times)
        max_time = max(valid_times)
        avg_time = statistics.mean(valid_times)
        median_time = statistics.median(valid_times)
        std_dev = statistics.stdev(valid_times) if len(valid_times) > 1 else 0.0
        throughput = 1.0 / avg_time if avg_time > 0 else 0.0
        avg_memory = statistics.mean(memory_usage_samples)
        success_rate = successful_operations / iterations
        
        metrics = PerformanceMetrics(
            operation=operation,
            provider_name=provider_name,
            min_time=min_time,
            max_time=max_time,
            avg_time=avg_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput,
            memory_usage_mb=avg_memory,
            success_rate=success_rate
        )
        
        self.benchmark_results.append(metrics)
        return metrics
    
    def benchmark_all_operations(self, provider_name: str, iterations: int = 100) -> List[PerformanceMetrics]:
        """Benchmark all operations for a provider."""
        operations = [
            ("analyze_symbol", AnalyzeParams(symbol_name="test_symbol")),
            ("rename_symbol", RenameParams(symbol_name="old_name", new_name="new_name")),
            ("extract_element", ExtractParams(source="function.lambda_1", new_name="extracted")),
            ("find_symbols", FindParams(pattern="test*")),
            ("show_function", ShowParams(function_name="test_function"))
        ]
        
        results = []
        for operation, params in operations:
            metrics = self.benchmark_operation(provider_name, operation, params, iterations)
            results.append(metrics)
        
        return results
    
    def compare_providers(self, operation: str, params: Any, iterations: int = 100) -> Dict[str, PerformanceMetrics]:
        """Compare all registered providers for a specific operation."""
        comparison_results = {}
        
        for provider_name in self.providers:
            metrics = self.benchmark_operation(provider_name, operation, params, iterations)
            comparison_results[provider_name] = metrics
        
        return comparison_results
    
    def test_scalability(self, provider_name: str, operation: str, base_params: Any, 
                        scale_factors: List[int] = None) -> ScalabilityMetrics:
        """Test provider scalability with increasing load."""
        if scale_factors is None:
            scale_factors = [1, 10, 50, 100, 500]
        
        execution_times = []
        memory_usage = []
        
        for scale_factor in scale_factors:
            # Create scaled parameters
            scaled_params = self._scale_params(base_params, scale_factor)
            
            # Benchmark with scaled parameters
            metrics = self.benchmark_operation(provider_name, operation, scaled_params, iterations=10)
            
            execution_times.append(metrics.avg_time)
            memory_usage.append(metrics.memory_usage_mb)
        
        # Calculate scalability metrics
        throughput_degradation = self._calculate_throughput_degradation(scale_factors, execution_times)
        scalability_score = self._calculate_scalability_score(scale_factors, execution_times)
        
        return ScalabilityMetrics(
            scale_factors=scale_factors,
            execution_times=execution_times,
            memory_usage=memory_usage,
            throughput_degradation=throughput_degradation,
            scalability_score=scalability_score
        )
    
    def detect_performance_regression(self, provider_name: str, operation: str, 
                                    baseline_metrics: PerformanceMetrics, 
                                    current_metrics: PerformanceMetrics,
                                    tolerance_percent: float = 10.0) -> Dict[str, Any]:
        """Detect performance regression by comparing to baseline."""
        regression_detected = False
        regressions = []
        
        # Check average time regression
        time_increase = ((current_metrics.avg_time - baseline_metrics.avg_time) / 
                        baseline_metrics.avg_time) * 100
        
        if time_increase > tolerance_percent:
            regression_detected = True
            regressions.append(f"Average time increased by {time_increase:.1f}%")
        
        # Check throughput regression
        throughput_decrease = ((baseline_metrics.throughput - current_metrics.throughput) / 
                              baseline_metrics.throughput) * 100
        
        if throughput_decrease > tolerance_percent:
            regression_detected = True
            regressions.append(f"Throughput decreased by {throughput_decrease:.1f}%")
        
        # Check memory usage increase
        memory_increase = ((current_metrics.memory_usage_mb - baseline_metrics.memory_usage_mb) / 
                          max(baseline_metrics.memory_usage_mb, 0.1)) * 100
        
        if memory_increase > tolerance_percent * 2:  # More tolerant for memory
            regression_detected = True
            regressions.append(f"Memory usage increased by {memory_increase:.1f}%")
        
        # Check success rate decrease
        success_decrease = ((baseline_metrics.success_rate - current_metrics.success_rate) / 
                           baseline_metrics.success_rate) * 100
        
        if success_decrease > 5.0:  # 5% tolerance for success rate
            regression_detected = True
            regressions.append(f"Success rate decreased by {success_decrease:.1f}%")
        
        return {
            "regression_detected": regression_detected,
            "regressions": regressions,
            "time_change_percent": time_increase,
            "throughput_change_percent": -throughput_decrease,
            "memory_change_percent": memory_increase,
            "success_rate_change_percent": -success_decrease
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _scale_params(self, base_params: Any, scale_factor: int) -> Any:
        """Scale parameters for load testing."""
        # For most operations, we can't easily scale parameters
        # This is a simplified implementation
        if isinstance(base_params, FindParams):
            # For find operations, we could search for more patterns
            return FindParams(pattern=f"{base_params.pattern}*{scale_factor}")
        else:
            # For other operations, return base params
            return base_params
    
    def _calculate_throughput_degradation(self, scale_factors: List[int], execution_times: List[float]) -> float:
        """Calculate throughput degradation across scale factors."""
        if len(execution_times) < 2:
            return 0.0
        
        initial_throughput = 1.0 / execution_times[0] if execution_times[0] > 0 else 0.0
        final_throughput = 1.0 / execution_times[-1] if execution_times[-1] > 0 else 0.0
        
        if initial_throughput == 0:
            return float('inf')
        
        degradation = ((initial_throughput - final_throughput) / initial_throughput) * 100
        return max(0.0, degradation)
    
    def _calculate_scalability_score(self, scale_factors: List[int], execution_times: List[float]) -> float:
        """Calculate scalability score (lower is better)."""
        if len(execution_times) < 2:
            return 0.0
        
        # Calculate the slope of execution time vs scale factor
        # Perfect linear scaling would have a slope of 1
        time_ratios = [execution_times[i] / execution_times[0] for i in range(len(execution_times))]
        scale_ratios = [scale_factors[i] / scale_factors[0] for i in range(len(scale_factors))]
        
        # Calculate average deviation from linear scaling
        deviations = []
        for i in range(1, len(time_ratios)):
            expected_ratio = scale_ratios[i]
            actual_ratio = time_ratios[i]
            deviation = abs(actual_ratio - expected_ratio) / expected_ratio
            deviations.append(deviation)
        
        return statistics.mean(deviations) if deviations else 0.0


class TestProviderPerformanceBenchmarks:
    """Test provider performance benchmarking."""
    
    def setup_method(self):
        """Set up performance testing environment."""
        self.performance_suite = ProviderPerformanceSuite()
        self.rope_provider = MockRopeProvider()
        self.tree_sitter_provider = MockTreeSitterProvider()
        
        self.performance_suite.register_provider(self.rope_provider)
        self.performance_suite.register_provider(self.tree_sitter_provider)
    
    def test_single_operation_benchmark(self):
        """Test benchmarking a single operation."""
        metrics = self.performance_suite.benchmark_operation(
            "mock_rope",
            "analyze_symbol",
            AnalyzeParams(symbol_name="test_symbol"),
            iterations=50
        )
        
        assert metrics.operation == "analyze_symbol"
        assert metrics.provider_name == "mock_rope"
        assert metrics.min_time >= 0
        assert metrics.avg_time >= metrics.min_time
        assert metrics.max_time >= metrics.avg_time
        assert metrics.success_rate > 0.9  # Should be mostly successful
        assert metrics.throughput > 0
    
    def test_all_operations_benchmark(self):
        """Test benchmarking all operations for a provider."""
        results = self.performance_suite.benchmark_all_operations("mock_rope", iterations=20)
        
        assert len(results) == 5  # All operations
        
        operations = [r.operation for r in results]
        assert "analyze_symbol" in operations
        assert "rename_symbol" in operations
        assert "extract_element" in operations
        assert "find_symbols" in operations
        assert "show_function" in operations
        
        # All should have reasonable performance
        for result in results:
            assert result.avg_time < 1.0  # Should be under 1 second
            assert result.success_rate > 0.8  # Should be mostly successful
    
    def test_provider_comparison(self):
        """Test comparing multiple providers."""
        comparison = self.performance_suite.compare_providers(
            "analyze_symbol",
            AnalyzeParams(symbol_name="test_symbol"),
            iterations=30
        )
        
        assert "mock_rope" in comparison
        assert "mock_tree_sitter" in comparison
        
        rope_metrics = comparison["mock_rope"]
        tree_sitter_metrics = comparison["mock_tree_sitter"]
        
        # Both should be successful
        assert rope_metrics.success_rate > 0.8
        assert tree_sitter_metrics.success_rate > 0.8
        
        # Both should have reasonable performance
        assert rope_metrics.avg_time < 1.0
        assert tree_sitter_metrics.avg_time < 1.0
    
    def test_scalability_testing(self):
        """Test provider scalability."""
        scalability_metrics = self.performance_suite.test_scalability(
            "mock_rope",
            "find_symbols",
            FindParams(pattern="test*"),
            scale_factors=[1, 5, 10, 20]
        )
        
        assert len(scalability_metrics.scale_factors) == 4
        assert len(scalability_metrics.execution_times) == 4
        assert len(scalability_metrics.memory_usage) == 4
        
        # Execution times should generally increase with scale
        # (though mock providers might not show this)
        assert all(t >= 0 for t in scalability_metrics.execution_times)
        
        # Scalability score should be finite
        assert scalability_metrics.scalability_score >= 0
    
    def test_performance_regression_detection(self):
        """Test performance regression detection."""
        # Create baseline metrics
        baseline = PerformanceMetrics(
            operation="analyze_symbol",
            provider_name="mock_rope",
            min_time=0.01,
            max_time=0.05,
            avg_time=0.02,
            median_time=0.02,
            std_dev=0.005,
            throughput=50.0,
            memory_usage_mb=10.0,
            success_rate=1.0
        )
        
        # Create current metrics with regression
        current = PerformanceMetrics(
            operation="analyze_symbol",
            provider_name="mock_rope",
            min_time=0.02,
            max_time=0.08,
            avg_time=0.035,  # 75% slower
            median_time=0.03,
            std_dev=0.01,
            throughput=28.5,  # Correspondingly lower
            memory_usage_mb=15.0,  # 50% more memory
            success_rate=0.95  # 5% lower success rate
        )
        
        regression_result = self.performance_suite.detect_performance_regression(
            "mock_rope",
            "analyze_symbol",
            baseline,
            current,
            tolerance_percent=10.0
        )
        
        assert regression_result["regression_detected"] == True
        assert len(regression_result["regressions"]) > 0
        assert "Average time increased" in str(regression_result["regressions"])
    
    def test_no_performance_regression(self):
        """Test when no performance regression is detected."""
        # Create baseline metrics
        baseline = PerformanceMetrics(
            operation="analyze_symbol",
            provider_name="mock_rope",
            min_time=0.01,
            max_time=0.05,
            avg_time=0.02,
            median_time=0.02,
            std_dev=0.005,
            throughput=50.0,
            memory_usage_mb=10.0,
            success_rate=1.0
        )
        
        # Create current metrics without significant regression
        current = PerformanceMetrics(
            operation="analyze_symbol",
            provider_name="mock_rope",
            min_time=0.01,
            max_time=0.05,
            avg_time=0.021,  # Only 5% slower
            median_time=0.02,
            std_dev=0.005,
            throughput=47.6,
            memory_usage_mb=10.5,  # Only 5% more memory
            success_rate=1.0
        )
        
        regression_result = self.performance_suite.detect_performance_regression(
            "mock_rope",
            "analyze_symbol",
            baseline,
            current,
            tolerance_percent=10.0
        )
        
        assert regression_result["regression_detected"] == False
        assert len(regression_result["regressions"]) == 0


class TestProviderPerformanceWithFactory:
    """Test performance with factory-created providers."""
    
    def setup_method(self):
        """Set up factory-based performance tests."""
        self.factory = MockProviderFactory()
        self.performance_suite = ProviderPerformanceSuite()
    
    def test_latency_simulation_benchmark(self):
        """Test benchmarking providers with different latencies."""
        fast_provider = self.factory.create_fast_provider("fast_provider")
        slow_provider = self.factory.create_slow_provider("slow_provider", latency_ms=100)
        
        self.performance_suite.register_provider(fast_provider)
        self.performance_suite.register_provider(slow_provider)
        
        # Benchmark both providers
        fast_metrics = self.performance_suite.benchmark_operation(
            "fast_provider",
            "analyze_symbol",
            AnalyzeParams(symbol_name="test"),
            iterations=20
        )
        
        slow_metrics = self.performance_suite.benchmark_operation(
            "slow_provider",
            "analyze_symbol", 
            AnalyzeParams(symbol_name="test"),
            iterations=20
        )
        
        # Slow provider should be significantly slower
        assert slow_metrics.avg_time > fast_metrics.avg_time
        assert slow_metrics.avg_time >= 0.1  # At least 100ms due to latency
        
        # Fast provider should have higher throughput
        assert fast_metrics.throughput > slow_metrics.throughput
    
    def test_failure_rate_performance_impact(self):
        """Test performance impact of provider failures."""
        failing_provider = self.factory.create_failing_provider(
            "failing_provider",
            failure_mode="error",
            failure_operations=["analyze_symbol"]
        )
        
        self.performance_suite.register_provider(failing_provider)
        
        metrics = self.performance_suite.benchmark_operation(
            "failing_provider",
            "analyze_symbol",
            AnalyzeParams(symbol_name="test"),
            iterations=20
        )
        
        # Should have low success rate
        assert metrics.success_rate < 0.5
        
        # Should still measure timing (for error handling)
        assert metrics.avg_time >= 0
    
    def test_memory_usage_tracking(self):
        """Test memory usage tracking during benchmarks."""
        basic_provider = self.factory.create_basic_provider("memory_test_provider")
        self.performance_suite.register_provider(basic_provider)
        
        metrics = self.performance_suite.benchmark_operation(
            "memory_test_provider",
            "analyze_symbol",
            AnalyzeParams(symbol_name="test"),
            iterations=50
        )
        
        # Should track memory usage
        assert metrics.memory_usage_mb >= 0
        
        # Memory usage should be reasonable for mock provider
        assert metrics.memory_usage_mb < 100  # Less than 100MB


class TestProviderLoadTesting:
    """Test provider behavior under load."""
    
    def setup_method(self):
        """Set up load testing environment."""
        self.performance_suite = ProviderPerformanceSuite()
        self.rope_provider = MockRopeProvider()
        self.performance_suite.register_provider(self.rope_provider)
    
    def test_high_frequency_operations(self):
        """Test provider performance with high-frequency operations."""
        # Test with many iterations to simulate load
        metrics = self.performance_suite.benchmark_operation(
            "mock_rope",
            "analyze_symbol",
            AnalyzeParams(symbol_name="test_symbol"),
            iterations=500
        )
        
        # Should maintain good performance even with many operations
        assert metrics.success_rate > 0.95
        assert metrics.avg_time < 0.1  # Should be fast for mock provider
        assert metrics.std_dev < metrics.avg_time  # Reasonable consistency
    
    def test_concurrent_operation_simulation(self):
        """Test simulated concurrent operations."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def worker():
            metrics = self.performance_suite.benchmark_operation(
                "mock_rope",
                "analyze_symbol",
                AnalyzeParams(symbol_name="test_symbol"),
                iterations=50
            )
            results_queue.put(metrics)
        
        # Start multiple worker threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 3
        
        # All should be successful
        for metrics in results:
            assert metrics.success_rate > 0.9
            assert metrics.avg_time < 1.0
    
    def test_resource_exhaustion_simulation(self):
        """Test provider behavior under resource constraints."""
        # Simulate resource exhaustion by running many operations rapidly
        start_time = time.time()
        operation_count = 0
        
        while time.time() - start_time < 2.0:  # Run for 2 seconds
            result = self.rope_provider.analyze_symbol(AnalyzeParams(symbol_name=f"symbol_{operation_count}"))
            operation_count += 1
            
            # Provider should continue to respond
            assert result is not None
            assert hasattr(result, 'success')
        
        # Should complete many operations
        assert operation_count > 10
        
        # Calculate approximate throughput
        elapsed_time = time.time() - start_time
        throughput = operation_count / elapsed_time
        
        # Should maintain reasonable throughput
        assert throughput > 5  # At least 5 operations per second


@pytest.mark.performance
class TestPerformanceRegression:
    """Test performance regression detection and monitoring."""
    
    def setup_method(self):
        """Set up regression testing."""
        self.performance_suite = ProviderPerformanceSuite()
        self.rope_provider = MockRopeProvider()
        self.performance_suite.register_provider(self.rope_provider)
    
    def test_baseline_establishment(self):
        """Test establishing performance baselines."""
        # Run baseline benchmark
        baseline_metrics = self.performance_suite.benchmark_operation(
            "mock_rope",
            "analyze_symbol",
            AnalyzeParams(symbol_name="baseline_test"),
            iterations=100
        )
        
        # Store as baseline
        self.performance_suite.baseline_metrics["mock_rope_analyze"] = baseline_metrics
        
        # Baseline should have reasonable values
        assert baseline_metrics.avg_time > 0
        assert baseline_metrics.success_rate > 0.9
        assert baseline_metrics.throughput > 0
    
    def test_performance_monitoring(self):
        """Test continuous performance monitoring."""
        baselines = {}
        
        # Establish baselines for multiple operations
        operations = [
            ("analyze_symbol", AnalyzeParams(symbol_name="test")),
            ("rename_symbol", RenameParams(symbol_name="old", new_name="new")),
            ("find_symbols", FindParams(pattern="test*"))
        ]
        
        for operation, params in operations:
            baseline = self.performance_suite.benchmark_operation(
                "mock_rope",
                operation,
                params,
                iterations=50
            )
            baselines[operation] = baseline
        
        # Simulate later monitoring
        for operation, params in operations:
            current = self.performance_suite.benchmark_operation(
                "mock_rope",
                operation,
                params,
                iterations=50
            )
            
            regression_check = self.performance_suite.detect_performance_regression(
                "mock_rope",
                operation,
                baselines[operation],
                current,
                tolerance_percent=20.0  # More tolerant for test environment
            )
            
            # Should not detect regression in stable mock environment
            assert not regression_check["regression_detected"]
    
    def test_benchmark_result_storage(self):
        """Test storing and retrieving benchmark results."""
        # Run multiple benchmarks
        operations = ["analyze_symbol", "rename_symbol", "find_symbols"]
        
        for operation in operations:
            params = self._get_sample_params(operation)
            self.performance_suite.benchmark_operation(
                "mock_rope",
                operation,
                params,
                iterations=20
            )
        
        # Check that results were stored
        assert len(self.performance_suite.benchmark_results) == 3
        
        # Results should contain expected operations
        stored_operations = [r.operation for r in self.performance_suite.benchmark_results]
        for operation in operations:
            assert operation in stored_operations
    
    def _get_sample_params(self, operation: str) -> Any:
        """Get sample parameters for operation."""
        if operation == "analyze_symbol":
            return AnalyzeParams(symbol_name="test_symbol")
        elif operation == "rename_symbol":
            return RenameParams(symbol_name="old_name", new_name="new_name")
        elif operation == "extract_element":
            return ExtractParams(source="function.lambda_1", new_name="extracted")
        elif operation == "find_symbols":
            return FindParams(pattern="test*")
        elif operation == "show_function":
            return ShowParams(function_name="test_function")
        else:
            raise ValueError(f"Unknown operation: {operation}")


if __name__ == "__main__":
    # Run performance benchmarks as standalone script
    print("Running Provider Performance Benchmarks...")
    
    suite = ProviderPerformanceSuite()
    rope_provider = MockRopeProvider()
    suite.register_provider(rope_provider)
    
    # Benchmark all operations
    print("\nBenchmarking all operations for Rope provider:")
    results = suite.benchmark_all_operations("mock_rope", iterations=100)
    
    for result in results:
        print(f"{result.operation}: {result.avg_time:.4f}s avg, "
              f"{result.throughput:.1f} ops/sec, "
              f"{result.success_rate:.1%} success")
    
    # Test scalability
    print("\nTesting scalability:")
    scalability = suite.test_scalability(
        "mock_rope",
        "find_symbols",
        FindParams(pattern="test*"),
        scale_factors=[1, 5, 10, 20, 50]
    )
    
    print(f"Scalability score: {scalability.scalability_score:.3f}")
    print(f"Throughput degradation: {scalability.throughput_degradation:.1f}%")
    
    print("\nPerformance benchmarking complete.")