"""
Provider testing framework utilities and mocks.

This module provides comprehensive testing infrastructure for refactoring providers,
including test frameworks, builders, validators, and performance benchmarks.
"""

import time
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from unittest.mock import Mock
from datetime import datetime

from refactor_mcp.models.params import AnalyzeParams, RenameParams, ExtractParams, FindParams, ShowParams
from refactor_mcp.models.responses import (
    AnalysisResult, RenameResult
)
from refactor_mcp.models.errors import ErrorResponse
from refactor_mcp.models import SymbolInfo, ElementInfo
from refactor_mcp.providers.base import RefactoringProvider


@dataclass
class ProviderTestCase:
    """Represents a single test case for a provider."""
    name: str
    operation: str
    params: Union[AnalyzeParams, RenameParams, ExtractParams, FindParams, ShowParams]
    expected_success: bool = True
    expected_error_type: Optional[str] = None
    timeout_ms: Optional[int] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    validation_rules: List[str] = field(default_factory=list)


@dataclass
class ProviderTestResult:
    """Result of executing a test case against a provider."""
    success: bool
    provider_name: str
    test_case_name: str
    operation: str
    execution_time_ms: float
    memory_usage_mb: Optional[float] = None
    response: Optional[Any] = None
    error: Optional[Exception] = None
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class ComplianceResult:
    """Result of provider compliance validation."""
    is_compliant: bool
    missing_methods: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    error_scenarios_tested: int = 0
    handles_errors_correctly: bool = True


@dataclass
class PerformanceResult:
    """Result of performance benchmarking."""
    provider_name: str
    operation: str
    execution_time: float
    memory_usage: Optional[float]
    success: bool
    scale_factor: Optional[int] = None


@dataclass
class BenchmarkComparison:
    """Comparison results between multiple providers."""
    provider_results: Dict[str, List[PerformanceResult]]
    performance_ranking: List[str]
    fastest_provider: str
    slowest_provider: str
    average_times: Dict[str, float]


class ProviderTestFramework:
    """Core testing framework for refactoring providers."""
    
    def __init__(self):
        self.providers: Dict[str, RefactoringProvider] = {}
        self.test_cases: List[ProviderTestCase] = []
        self.results: List[ProviderTestResult] = []
    
    def register_provider(self, provider: RefactoringProvider):
        """Register a provider for testing."""
        provider_name = getattr(provider, 'name', provider.get_metadata().name)
        self.providers[provider_name] = provider
    
    def get_provider(self, name: str) -> Optional[RefactoringProvider]:
        """Get a registered provider by name."""
        return self.providers.get(name)
    
    def execute_test_case(self, test_case: ProviderTestCase, provider_name: str) -> ProviderTestResult:
        """Execute a single test case against a provider."""
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not registered")
        
        start_time = time.time()
        
        try:
            # Get the operation method
            operation_method = getattr(provider, test_case.operation)
            
            # Execute the operation
            response = operation_method(test_case.params)
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Validate response
            validation_errors = self._validate_response(response, test_case)
            
            success = (
                test_case.expected_success and 
                hasattr(response, 'success') and 
                response.success and
                len(validation_errors) == 0
            )
            
            return ProviderTestResult(
                success=success,
                provider_name=provider_name,
                test_case_name=test_case.name,
                operation=test_case.operation,
                execution_time_ms=execution_time,
                response=response,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            success = not test_case.expected_success
            
            return ProviderTestResult(
                success=success,
                provider_name=provider_name,
                test_case_name=test_case.name,
                operation=test_case.operation,
                execution_time_ms=execution_time,
                error=e
            )
    
    def execute_test_batch(self, test_cases: List[ProviderTestCase], provider_name: str) -> List[ProviderTestResult]:
        """Execute multiple test cases against a provider."""
        results = []
        for test_case in test_cases:
            result = self.execute_test_case(test_case, provider_name)
            results.append(result)
            self.results.append(result)
        return results
    
    def _validate_response(self, response: Any, test_case: ProviderTestCase) -> List[str]:
        """Validate response against test case requirements."""
        violations = []
        
        # Check basic response structure
        if not hasattr(response, 'success'):
            violations.append("Response missing 'success' field")
        
        # Apply validation rules
        for rule in test_case.validation_rules:
            if rule == "has_symbol_info" and test_case.operation == "analyze_symbol":
                if not hasattr(response, 'symbol_info') or response.symbol_info is None:
                    violations.append("Missing symbol_info in analysis result")
            
            elif rule == "has_references" and test_case.operation == "analyze_symbol":
                if not hasattr(response, 'references'):
                    violations.append("Missing references in analysis result")
            
            elif rule == "valid_qualified_name" and hasattr(response, 'qualified_name'):
                if not response.qualified_name or '.' not in response.qualified_name:
                    violations.append("Invalid qualified name format")
        
        return violations


class ProviderTestBuilder:
    """Builder for creating provider test cases."""
    
    def __init__(self):
        self.test_cases: List[ProviderTestCase] = []
    
    def add_analyze_test(self, symbol_name: str, expected_success: bool = True) -> 'ProviderTestBuilder':
        """Add an analyze symbol test case."""
        test_case = ProviderTestCase(
            name=f"analyze_{symbol_name}",
            operation="analyze_symbol",
            params=AnalyzeParams(symbol_name=symbol_name),
            expected_success=expected_success,
            validation_rules=["has_symbol_info", "has_references"]
        )
        self.test_cases.append(test_case)
        return self
    
    def add_rename_test(self, old_name: str, new_name: str, expected_success: bool = True) -> 'ProviderTestBuilder':
        """Add a rename symbol test case."""
        test_case = ProviderTestCase(
            name=f"rename_{old_name}_to_{new_name}",
            operation="rename_symbol",
            params=RenameParams(symbol_name=old_name, new_name=new_name),
            expected_success=expected_success,
            validation_rules=["valid_qualified_name"]
        )
        self.test_cases.append(test_case)
        return self
    
    def add_extract_test(self, source: str, new_name: str, expected_success: bool = True) -> 'ProviderTestBuilder':
        """Add an extract element test case."""
        test_case = ProviderTestCase(
            name=f"extract_{source}_as_{new_name}",
            operation="extract_element",
            params=ExtractParams(source=source, new_name=new_name),
            expected_success=expected_success
        )
        self.test_cases.append(test_case)
        return self
    
    def add_validation_scenario(self, scenario_type: str) -> 'ProviderTestBuilder':
        """Add validation scenario test cases."""
        scenarios = {
            "symbol_not_found": ProviderTestCase(
                name="symbol_not_found",
                operation="analyze_symbol",
                params=AnalyzeParams(symbol_name="nonexistent_symbol"),
                expected_success=False,
                expected_error_type="symbol_not_found"
            ),
            "invalid_extract_source": ProviderTestCase(
                name="invalid_extract_source",
                operation="extract_element",
                params=ExtractParams(source="invalid_format", new_name="test"),
                expected_success=False,
                expected_error_type="invalid_source"
            ),
            "rename_conflict": ProviderTestCase(
                name="rename_conflict",
                operation="rename_symbol",
                params=RenameParams(symbol_name="existing_symbol", new_name="another_existing_symbol"),
                expected_success=False,
                expected_error_type="naming_conflict"
            )
        }
        
        if scenario_type in scenarios:
            self.test_cases.append(scenarios[scenario_type])
        
        return self
    
    def add_performance_test(self, test_name: str, **kwargs) -> 'ProviderTestBuilder':
        """Add performance test case."""
        if test_name == "large_symbol_set":
            symbol_count = kwargs.get('symbol_count', 100)
            test_case = ProviderTestCase(
                name=f"large_symbol_set_{symbol_count}",
                operation="find_symbols",
                params=FindParams(pattern="*"),
                performance_metrics={"expected_symbol_count": symbol_count, "max_time_ms": 5000}
            )
        elif test_name == "deep_nesting":
            nesting_level = kwargs.get('nesting_level', 5)
            test_case = ProviderTestCase(
                name=f"deep_nesting_{nesting_level}",
                operation="show_function",
                params=ShowParams(function_name=f"deeply_nested_function_level_{nesting_level}"),
                performance_metrics={"nesting_level": nesting_level, "max_time_ms": 3000}
            )
        else:
            raise ValueError(f"Unknown performance test type: {test_name}")
        
        self.test_cases.append(test_case)
        return self
    
    def from_test_data(self, test_data: Dict[str, Any]) -> 'ProviderTestBuilder':
        """Create test cases from generated test data."""
        # This would be implemented to convert test data into test cases
        symbols = test_data.get('symbols', [])
        for symbol in symbols:
            self.add_analyze_test(symbol['name'])
        
        return self
    
    def build(self) -> List[ProviderTestCase]:
        """Build and return the test cases."""
        return self.test_cases.copy()


class ProviderComplianceValidator:
    """Validates provider compliance with the RefactoringProvider protocol."""
    
    def __init__(self):
        self.validation_rules = [
            "has_required_methods",
            "returns_correct_types",
            "handles_errors_gracefully",
            "follows_naming_conventions"
        ]
    
    def validate_interface(self, provider: RefactoringProvider) -> ComplianceResult:
        """Validate provider interface compliance."""
        required_methods = [
            'supports_language', 'get_capabilities', 'analyze_symbol',
            'find_symbols', 'show_function', 'rename_symbol', 'extract_element'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(provider, method):
                missing_methods.append(method)
        
        violations = []
        if not hasattr(provider, 'name'):
            violations.append("Provider missing 'name' attribute")
        
        return ComplianceResult(
            is_compliant=len(missing_methods) == 0 and len(violations) == 0,
            missing_methods=missing_methods,
            violations=violations
        )
    
    def validate_response(self, response: Any, operation: str) -> ComplianceResult:
        """Validate response format compliance."""
        violations = []
        
        if not hasattr(response, 'success'):
            violations.append("Response missing 'success' field")
        
        # Operation-specific validations
        if operation == "analyze_symbol":
            if hasattr(response, 'success') and response.success:
                if not hasattr(response, 'symbol_info'):
                    violations.append("AnalysisResult missing symbol_info")
                if not hasattr(response, 'references'):
                    violations.append("AnalysisResult missing references")
        
        elif operation == "rename_symbol":
            if hasattr(response, 'success') and response.success:
                if not hasattr(response, 'old_name') or not hasattr(response, 'new_name'):
                    violations.append("RenameResult missing name fields")
        
        return ComplianceResult(
            is_compliant=len(violations) == 0,
            violations=violations
        )
    
    def validate_error_handling(self, provider: RefactoringProvider) -> ComplianceResult:
        """Validate provider error handling."""
        error_scenarios = [
            AnalyzeParams(symbol_name="nonexistent_symbol"),
            RenameParams(symbol_name="invalid", new_name=""),
            ExtractParams(source="invalid.format", new_name="test")
        ]
        
        handles_errors_correctly = True
        scenarios_tested = 0
        
        for scenario in error_scenarios:
            try:
                if isinstance(scenario, AnalyzeParams):
                    result = provider.analyze_symbol(scenario)
                elif isinstance(scenario, RenameParams):
                    result = provider.rename_symbol(scenario)
                elif isinstance(scenario, ExtractParams):
                    result = provider.extract_element(scenario)
                
                scenarios_tested += 1
                
                # Check if error was handled gracefully
                if not hasattr(result, 'success') or result.success:
                    handles_errors_correctly = False
                
            except Exception:
                # Provider should return error responses, not raise exceptions
                handles_errors_correctly = False
        
        return ComplianceResult(
            is_compliant=handles_errors_correctly,
            error_scenarios_tested=scenarios_tested,
            handles_errors_correctly=handles_errors_correctly
        )
    
    def validate_provider(self, provider: RefactoringProvider, test_results: List[ProviderTestResult]) -> ComplianceResult:
        """Comprehensive provider validation."""
        interface_result = self.validate_interface(provider)
        error_result = self.validate_error_handling(provider)
        
        all_violations = interface_result.violations + error_result.violations
        
        return ComplianceResult(
            is_compliant=interface_result.is_compliant and error_result.is_compliant,
            missing_methods=interface_result.missing_methods,
            violations=all_violations,
            error_scenarios_tested=error_result.error_scenarios_tested,
            handles_errors_correctly=error_result.handles_errors_correctly
        )


class ProviderPerformanceBenchmark:
    """Performance benchmarking for providers."""
    
    def __init__(self):
        self.providers: Dict[str, RefactoringProvider] = {}
        self.benchmark_suites: List[str] = ["basic_operations", "scalability", "stress_test"]
    
    def add_provider(self, provider: RefactoringProvider):
        """Add provider to benchmark."""
        self.providers[provider.name] = provider
    
    def time_operation(self, provider: RefactoringProvider, operation: str, params: Any) -> PerformanceResult:
        """Measure execution time for a single operation."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            method = getattr(provider, operation)
            result = method(params)
            
            execution_time = time.time() - start_time
            memory_usage = self._get_memory_usage() - start_memory
            
            success = hasattr(result, 'success') and result.success
            
            return PerformanceResult(
                provider_name=provider.name,
                operation=operation,
                execution_time=execution_time,
                memory_usage=memory_usage,
                success=success
            )
            
        except Exception:
            execution_time = time.time() - start_time
            return PerformanceResult(
                provider_name=provider.name,
                operation=operation,
                execution_time=execution_time,
                memory_usage=None,
                success=False
            )
    
    def run_comparison(self, operations: List[str]) -> BenchmarkComparison:
        """Compare multiple providers across operations."""
        provider_results = {}
        
        for provider_name, provider in self.providers.items():
            results = []
            for operation in operations:
                # Create sample params for each operation
                params = self._get_sample_params(operation)
                result = self.time_operation(provider, operation, params)
                results.append(result)
            provider_results[provider_name] = results
        
        # Calculate rankings
        average_times = {}
        for provider_name, results in provider_results.items():
            successful_results = [r for r in results if r.success]
            if successful_results:
                avg_time = sum(r.execution_time for r in successful_results) / len(successful_results)
                average_times[provider_name] = avg_time
            else:
                average_times[provider_name] = float('inf')
        
        performance_ranking = sorted(average_times.keys(), key=lambda p: average_times[p])
        
        return BenchmarkComparison(
            provider_results=provider_results,
            performance_ranking=performance_ranking,
            fastest_provider=performance_ranking[0] if performance_ranking else "",
            slowest_provider=performance_ranking[-1] if performance_ranking else "",
            average_times=average_times
        )
    
    def test_scalability(self, provider: RefactoringProvider, operation: str, scale_factors: List[int]) -> Dict[str, Any]:
        """Test provider scalability with different load levels."""
        scale_results = []
        
        for scale_factor in scale_factors:
            # Create scaled test data
            params = self._get_scaled_params(operation, scale_factor)
            result = self.time_operation(provider, operation, params)
            result.scale_factor = scale_factor
            scale_results.append(result)
        
        # Calculate scalability score (lower is better)
        times = [r.execution_time for r in scale_results if r.success]
        if len(times) >= 2:
            # Simple linear regression to measure scalability
            scalability_score = (times[-1] - times[0]) / (scale_factors[-1] - scale_factors[0])
        else:
            scalability_score = float('inf')
        
        return {
            'scale_results': scale_results,
            'scalability_score': scalability_score
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage (simplified implementation)."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0  # Fallback if psutil not available
    
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
    
    def _get_scaled_params(self, operation: str, scale_factor: int) -> Any:
        """Get scaled parameters for scalability testing."""
        if operation == "find_symbols":
            # Create pattern that would match scale_factor symbols
            return FindParams(pattern=f"*test_{scale_factor}*")
        else:
            return self._get_sample_params(operation)


class MockProviderFactory:
    """Factory for creating various types of mock providers."""
    
    def __init__(self):
        self.provider_templates = {}
    
    def create_basic_provider(self, name: str, languages: List[str] = None, capabilities: List[str] = None) -> RefactoringProvider:
        """Create a basic mock provider."""
        if languages is None:
            languages = ["python"]
        if capabilities is None:
            capabilities = ["analyze", "rename", "extract", "find", "show"]
        
        provider = Mock(spec=RefactoringProvider)
        provider.name = name
        provider.supports_language.return_value = True
        
        # Configure basic responses
        if "analyze" in capabilities:
            provider.analyze_symbol.return_value = AnalysisResult(
                success=True,
                symbol_info=SymbolInfo(
                    name="test", 
                    qualified_name="test.test", 
                    type="function",
                    definition_location="test.py:1",
                    scope="global"
                ),
                references=["test.py:1"],
                reference_count=1
            )
        
        if "rename" in capabilities:
            provider.rename_symbol.return_value = RenameResult(
                success=True,
                old_name="old",
                new_name="new",
                qualified_name="test.new",
                files_modified=["test.py"]
            )
        
        return provider
    
    def create_failing_provider(self, name: str, failure_mode: str = "error", failure_operations: List[str] = None) -> RefactoringProvider:
        """Create a provider that fails in specific ways."""
        provider = Mock(spec=RefactoringProvider)
        provider.name = name
        provider.supports_language.return_value = True
        
        if failure_operations is None:
            failure_operations = ["analyze_symbol"]
        
        def create_failure_method(operation: str):
            if failure_mode == "timeout":
                def timeout_method(*args, **kwargs):
                    time.sleep(0.2)  # Simulate timeout
                    raise TimeoutError(f"Operation {operation} timed out")
                return timeout_method
            elif failure_mode == "error":
                def error_method(*args, **kwargs):
                    return ErrorResponse(
                        success=False,
                        error_type="provider_error",
                        error_message=f"Provider failed on {operation}",
                        suggestions=[]
                    )
                return error_method
            else:
                def generic_failure(*args, **kwargs):
                    raise Exception(f"Generic failure in {operation}")
                return generic_failure
        
        for operation in failure_operations:
            setattr(provider, operation, create_failure_method(operation))
        
        return provider
    
    def create_slow_provider(self, name: str, latency_ms: int = 100) -> RefactoringProvider:
        """Create a provider with configurable latency."""
        provider = Mock(spec=RefactoringProvider)
        provider.name = name
        provider.supports_language.return_value = True
        
        def slow_method(*args, **kwargs):
            time.sleep(latency_ms / 1000.0)  # Convert ms to seconds
            return AnalysisResult(
                success=True,
                symbol_info=SymbolInfo(name="test", qualified_name="test.test", type="function"),
                references=["test.py:1"],
                reference_count=1
            )
        
        provider.analyze_symbol = slow_method
        provider.rename_symbol = slow_method
        provider.extract_element = slow_method
        provider.find_symbols = slow_method
        provider.show_function = slow_method
        
        return provider
    
    def create_fast_provider(self, name: str) -> RefactoringProvider:
        """Create a fast provider for comparison."""
        return self.create_basic_provider(name)


class ProviderTestDataGenerator:
    """Generates test data for provider testing."""
    
    def __init__(self):
        self.data_templates = {
            "symbols": ["function", "class", "variable", "module"],
            "complexity_levels": ["simple", "medium", "complex"],
            "code_patterns": ["nested_functions", "lambdas", "complex_expressions"]
        }
    
    def generate_symbols(self, count: int, types: List[str] = None, complexity_levels: List[str] = None) -> List[SymbolInfo]:
        """Generate symbol test data."""
        if types is None:
            types = ["function", "class", "variable"]
        if complexity_levels is None:
            complexity_levels = ["simple", "medium"]
        
        symbols = []
        for i in range(count):
            symbol_type = types[i % len(types)]
            complexity = complexity_levels[i % len(complexity_levels)]
            
            symbol = SymbolInfo(
                name=f"test_{symbol_type}_{i}",
                qualified_name=f"test_module.test_{symbol_type}_{i}",
                type=symbol_type,
                definition_location=f"test_file_{i}.py:{i+1}",
                scope="global" if complexity == "simple" else "class"
            )
            symbols.append(symbol)
        
        return symbols
    
    def generate_code_patterns(self, pattern_types: List[str], languages: List[str] = None) -> List[Dict[str, Any]]:
        """Generate code patterns for testing."""
        if languages is None:
            languages = ["python"]
        
        patterns = []
        
        for pattern_type in pattern_types:
            if pattern_type == "nested_functions":
                pattern = {
                    "code": "def outer():\n    def inner():\n        pass\n    return inner",
                    "extractable_elements": [
                        ElementInfo(id="inner_function", type="function", code="def inner():", location="line:2", extractable=True)
                    ]
                }
            elif pattern_type == "lambdas":
                pattern = {
                    "code": "process = lambda x: x * 2 if x > 0 else 0",
                    "extractable_elements": [
                        ElementInfo(id="lambda_1", type="lambda", code="lambda x: x * 2 if x > 0 else 0", location="line:1", extractable=True)
                    ]
                }
            elif pattern_type == "complex_expressions":
                pattern = {
                    "code": "result = [func(x) for x in data if condition(x) and x.value > threshold]",
                    "extractable_elements": [
                        ElementInfo(id="list_comp", type="expression", code="[func(x) for x in data if condition(x) and x.value > threshold]", location="line:1", extractable=True)
                    ]
                }
            else:
                continue
            
            patterns.append(pattern)
        
        return patterns
    
    def generate_edge_cases(self, categories: List[str]) -> List[Dict[str, Any]]:
        """Generate edge case scenarios."""
        edge_cases = []
        
        for category in categories:
            if category == "empty_input":
                edge_cases.append({
                    "scenario": "empty_symbol_name",
                    "params": AnalyzeParams(symbol_name=""),
                    "expected_behavior": "error_response"
                })
            elif category == "invalid_syntax":
                edge_cases.append({
                    "scenario": "invalid_extract_source",
                    "params": ExtractParams(source="invalid.format.too.many.dots", new_name="test"),
                    "expected_behavior": "error_response"
                })
            elif category == "boundary_conditions":
                edge_cases.append({
                    "scenario": "very_long_symbol_name",
                    "params": AnalyzeParams(symbol_name="a" * 1000),
                    "expected_behavior": "handles_gracefully"
                })
        
        return edge_cases
    
    def generate_complete_test_suite(self) -> Dict[str, Any]:
        """Generate a complete test suite."""
        return {
            "symbols": self.generate_symbols(10),
            "code_patterns": self.generate_code_patterns(["nested_functions", "lambdas"]),
            "edge_cases": self.generate_edge_cases(["empty_input", "invalid_syntax"])
        }


class ProviderTestReporter:
    """Generates reports from provider test results."""
    
    def __init__(self):
        self.results: List[ProviderTestResult] = []
    
    def aggregate_results(self, results: List[ProviderTestResult]) -> Dict[str, Any]:
        """Aggregate test results into summary."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        provider_summaries = {}
        for result in results:
            if result.provider_name not in provider_summaries:
                provider_summaries[result.provider_name] = {
                    "total": 0, "passed": 0, "failed": 0, "avg_time": 0.0
                }
            
            summary = provider_summaries[result.provider_name]
            summary["total"] += 1
            if result.success:
                summary["passed"] += 1
            else:
                summary["failed"] += 1
        
        # Calculate average times
        for provider_name in provider_summaries:
            provider_results = [r for r in results if r.provider_name == provider_name]
            if provider_results:
                avg_time = sum(r.execution_time_ms for r in provider_results) / len(provider_results)
                provider_summaries[provider_name]["avg_time"] = avg_time
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0.0,
            "provider_summaries": provider_summaries
        }
    
    def generate_html_report(self, results: List[ProviderTestResult]) -> str:
        """Generate HTML report."""
        summary = self.aggregate_results(results)
        
        html = f"""
        <html>
        <head><title>Provider Test Report</title></head>
        <body>
        <h1>Provider Test Report</h1>
        <h2>Summary</h2>
        <p>Total Tests: {summary['total_tests']}</p>
        <p>Passed: {summary['passed_tests']}</p>
        <p>Failed: {summary['failed_tests']}</p>
        <p>Success Rate: {summary['success_rate']:.1%}</p>
        
        <h2>Provider Details</h2>
        """
        
        for provider_name, provider_summary in summary['provider_summaries'].items():
            html += f"""
            <h3>{provider_name}</h3>
            <p>Tests: {provider_summary['total']} (Passed: {provider_summary['passed']}, Failed: {provider_summary['failed']})</p>
            <p>Average Time: {provider_summary['avg_time']:.2f}ms</p>
            """
        
        html += "</body></html>"
        return html
    
    def generate_json_report(self, results: List[ProviderTestResult]) -> str:
        """Generate JSON report."""
        summary = self.aggregate_results(results)
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "detailed_results": [
                {
                    "provider_name": r.provider_name,
                    "test_case_name": r.test_case_name,
                    "operation": r.operation,
                    "success": r.success,
                    "execution_time_ms": r.execution_time_ms,
                    "validation_errors": r.validation_errors,
                    "error": str(r.error) if r.error else None
                }
                for r in results
            ]
        }
        
        return json.dumps(report_data, indent=2)
    
    def generate_comprehensive_report(self, results: List[ProviderTestResult], compliance_result: ComplianceResult) -> Dict[str, Any]:
        """Generate comprehensive report including compliance."""
        summary = self.aggregate_results(results)
        
        return {
            "test_summary": summary,
            "compliance": {
                "is_compliant": compliance_result.is_compliant,
                "missing_methods": compliance_result.missing_methods,
                "violations": compliance_result.violations,
                "error_handling": compliance_result.handles_errors_correctly
            },
            "detailed_results": results,
            "timestamp": datetime.now().isoformat()
        }