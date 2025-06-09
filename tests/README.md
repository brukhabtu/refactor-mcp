# Testing Infrastructure

This directory contains comprehensive testing infrastructure for refactor-mcp, including fixtures, utilities, mock providers, and test data.

## Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # pytest fixtures and configuration
├── test_utils.py            # Testing utilities and helpers
├── test_infrastructure_demo.py  # Demonstrates infrastructure usage
├── data/                    # Test data and sample files
│   ├── sample_module.py     # Basic Python module for testing
│   ├── complex_project.py   # Advanced patterns for testing
│   └── sample_package/      # Multi-file package structure
└── mocks/                   # Mock implementations
    ├── providers.py         # Mock refactoring providers
    ├── engines.py           # Mock refactoring engines
    └── builders.py          # Builder patterns for test objects
```

## Key Features

### 1. pytest Fixtures (`conftest.py`)

- **`temp_dir`**: Clean temporary directory for each test
- **`test_project_dir`**: Pre-populated Python project with sample files
- **`mock_provider`**: Ready-to-use mock refactoring provider
- **`sample_*_result`**: Pre-built result objects for testing
- **`symbol_test_cases`**: Parametrized test data for different symbol types

### 2. Testing Utilities (`test_utils.py`)

- **Assertion helpers**: `assert_valid_symbol_info()`, `assert_successful_result()`, etc.
- **File management**: `TestFileManager` for creating test files and projects
- **Code comparison**: `compare_python_code()`, `validate_python_syntax()`
- **Builder patterns**: `SymbolInfoBuilder`, `ElementInfoBuilder`, etc.
- **Test decorators**: `@unit_test`, `@integration_test`, `@slow_test`

### 3. Mock Providers (`mocks/providers.py`)

- **`MockRopeProvider`**: Realistic rope-like behavior with sample data
- **`MockTreeSitterProvider`**: Multi-language provider simulation
- **`FailingProvider`**: Always returns errors for testing error handling
- **`ConfigurableProvider`**: Fully customizable responses for specific scenarios

### 4. Mock Engines (`mocks/engines.py`)

- **`MockRefactoringEngine`**: Complete engine simulation with provider management
- **`MockEngineBuilder`**: Fluent interface for building test engines
- **`MockOperationTracker`**: Simulates operation tracking and history

### 5. Builder Patterns (`mocks/builders.py`)

- **`MockProviderBuilder`**: Build providers with specific behaviors
- **`MockResultBuilder`**: Create result objects with realistic data
- **`TestScenarioBuilder`**: Build complete test scenarios

## Usage Examples

### Basic Test with Fixtures

```python
def test_symbol_analysis(mock_provider, sample_symbol_info):
    """Test symbol analysis with fixtures."""
    params = AnalyzeParams(symbol_name="test_function")
    result = mock_provider.analyze_symbol(params)
    
    assert_successful_result(result)
    assert_valid_symbol_info(result.symbol_info)
```

### Using Test File Management

```python
def test_file_operations(temp_dir):
    """Test file operations with temporary directory."""
    manager = TestFileManager(temp_dir)
    
    # Create test files
    python_file = manager.create_python_file("module", "def func(): pass")
    package_dir = manager.create_package("mypackage")
    
    # Use in tests
    assert python_file.exists()
    assert (package_dir / "__init__.py").exists()
```

### Building Mock Providers

```python
def test_with_custom_provider():
    """Test with custom mock provider."""
    provider = (MockProviderBuilder("test_provider")
               .supports_languages("python", "javascript")
               .analyze_symbol_returns("test_func", 
                                     MockResultBuilder.analysis_result("test_func").build())
               .rename_symbol_raises("invalid_func", "symbol_not_found", "Not found")
               .build())
    
    # Use provider in tests
    result = provider.analyze_symbol(AnalyzeParams(symbol_name="test_func"))
    assert_successful_result(result)
```

### Complete Test Scenarios

```python
def test_refactoring_workflow():
    """Test complete refactoring workflow."""
    # Build test scenario
    scenario = (TestScenarioBuilder("workflow_test")
               .with_provider(MockRopeProvider())
               .with_mock_engine()
               .expect_analyze_result("target", analysis_result)
               .with_test_data("project_path", "/test/project")
               .build())
    
    engine = scenario["engine"]
    
    # Execute workflow
    analyze_result = engine.analyze_symbol(AnalyzeParams(symbol_name="target"))
    assert_successful_result(analyze_result)
```

### Integration Testing

```python
@integration_test
def test_provider_integration(test_project_dir):
    """Integration test with real file structure."""
    engine = MockRefactoringEngine()
    
    # Test find operation
    find_result = engine.find_symbols(FindParams(pattern="*user*"))
    assert_successful_result(find_result)
    
    # Test analysis
    if find_result.matches:
        symbol = find_result.matches[0]
        analyze_result = engine.analyze_symbol(AnalyzeParams(symbol_name=symbol.name))
        assert_successful_result(analyze_result)
```

## Test Markers

Use these markers to categorize tests:

- `@unit_test`: Fast, isolated unit tests
- `@integration_test`: Tests with multiple components
- `@slow_test`: Tests that take significant time

Run specific test types:
```bash
# Run only unit tests
uv run pytest -m unit

# Run excluding slow tests
uv run pytest -m "not slow"

# Run integration tests
uv run pytest -m integration
```

## Test Data

### Sample Files

- **`data/sample_module.py`**: Basic Python constructs for testing
- **`data/complex_project.py`**: Advanced patterns (async, decorators, etc.)
- **`data/sample_package/`**: Multi-file package with cross-references

### Realistic Test Data

All mock providers come with realistic test data:

- Symbol information with proper qualified names
- Extractable elements with location information
- Cross-references between modules
- Error scenarios with helpful suggestions

## Best Practices

1. **Use fixtures**: Prefer fixtures over manual setup in tests
2. **Assert with helpers**: Use `assert_valid_*()` functions for consistent validation
3. **Build with builders**: Use builder patterns for complex test objects
4. **Mark tests**: Use appropriate test markers for categorization
5. **Isolate tests**: Each test should be independent and clean up after itself

## Adding New Tests

1. Choose appropriate test file or create new one
2. Use existing fixtures and utilities when possible
3. Add new fixtures to `conftest.py` if needed
4. Document complex test scenarios
5. Use appropriate test markers

See `test_infrastructure_demo.py` for comprehensive examples of all infrastructure features.