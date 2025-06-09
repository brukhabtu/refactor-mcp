"""
Integration tests for Rope provider show_function operation.

Tests real-world scenarios with actual Python code examples.
"""
import tempfile
import os
from pathlib import Path

from refactor_mcp.providers.rope.rope import RopeProvider
from refactor_mcp.models import ShowParams


class TestRopeProviderShow:
    """Test Rope provider show function functionality with real Python code"""
    
    def setup_method(self):
        """Set up test environment with temporary project"""
        self.temp_dir = tempfile.mkdtemp()
        self.provider = RopeProvider()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        self.provider._clear_cache()
    
    def create_file(self, filename: str, content: str) -> Path:
        """Create a test file with given content"""
        file_path = Path(self.temp_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path
    
    def test_show_function_with_lambdas(self):
        """Test showing a function that contains lambda expressions"""
        self.create_file("data_utils.py", """
def process_data_set(data_records):
    '''Process data records with various transformations'''
    
    # Filter valid records (lambda 1)
    valid_records = list(filter(lambda r: r.get('status') == 'active' and r.get('value') > 0, data_records))
    
    # Transform records (lambda 2)  
    transformed = list(map(lambda r: {
        'id': r['id'],
        'normalized_value': r['value'] / 100.0,
        'category': r.get('category', 'unknown').upper()
    }, valid_records))
    
    # Sort by value (lambda 3)
    sorted_data = sorted(transformed, key=lambda r: r['normalized_value'], reverse=True)
    
    return sorted_data
""")
        
        params = ShowParams(function_name="process_data_set")
        result = self.provider.show_function(params)
        
        # Expected: function found with 3 extractable lambda expressions
        assert result.success is True
        assert result.function_name == "process_data_set"
        assert len(result.extractable_elements) == 3
        
        # Verify lambda elements are detected
        lambda_elements = [e for e in result.extractable_elements if e.type == "lambda"]
        assert len(lambda_elements) == 3
        
        # Check that lambda IDs are properly generated
        lambda_ids = [e.id for e in lambda_elements]
        assert "process_data_set.lambda_1" in lambda_ids
        assert "process_data_set.lambda_2" in lambda_ids  
        assert "process_data_set.lambda_3" in lambda_ids
        
        # Verify all are marked as extractable
        for element in lambda_elements:
            assert element.extractable is True
            assert "lambda" in element.code
    
    def test_show_function_with_nested_expressions(self):
        """Test showing a function with nested and complex expressions"""
        self.create_file("analytics.py", """
class DataAnalyzer:
    def analyze_user_behavior(self, events):
        '''Analyze user behavior patterns from event data'''
        
        # Complex filtering with nested lambda
        filtered_events = list(filter(
            lambda e: e.get('type') in ['click', 'view', 'purchase'] and 
                     e.get('timestamp') > 1640995200 and
                     e.get('user_id') is not None,
            events
        ))
        
        # Group by user with complex transformation
        user_groups = {}
        for event in filtered_events:
            user_id = event['user_id']
            if user_id not in user_groups:
                user_groups[user_id] = []
            
            # Transform event data (could be lambda)
            processed_event = {
                'type': event['type'],
                'timestamp': event['timestamp'],
                'value': event.get('value', 0),
                'session_score': (
                    lambda t, v: t * 0.1 + v * 0.9 
                    if v > 0 else t * 0.05
                )(event['timestamp'], event.get('value', 0))
            }
            user_groups[user_id].append(processed_event)
        
        # Calculate user metrics with lambda
        user_metrics = {
            uid: {
                'event_count': len(events),
                'total_value': sum(map(lambda e: e['value'], events)),
                'avg_session_score': sum(map(lambda e: e['session_score'], events)) / len(events)
            }
            for uid, events in user_groups.items()
        }
        
        return user_metrics
""")
        
        params = ShowParams(function_name="analyze_user_behavior")
        result = self.provider.show_function(params)
        
        # Expected: function found with multiple lambda expressions
        assert result.success is True
        assert result.function_name == "analyze_user_behavior"
        assert len(result.extractable_elements) >= 4  # Multiple lambdas detected
        
        # Verify lambda elements are properly identified
        lambda_elements = [e for e in result.extractable_elements if e.type == "lambda"]
        assert len(lambda_elements) >= 4
        
        # Check location information is provided
        for element in lambda_elements:
            assert element.location is not None
            assert "analytics.py:" in element.location
            assert element.extractable is True
    
    def test_show_simple_function_no_extractable_elements(self):
        """Test showing a simple function with no extractable elements"""
        self.create_file("simple.py", """
def calculate_area(length, width):
    '''Calculate rectangle area'''
    if length <= 0 or width <= 0:
        raise ValueError("Dimensions must be positive")
    
    area = length * width
    return area
""")
        
        params = ShowParams(function_name="calculate_area")
        result = self.provider.show_function(params)
        
        # Expected: function found but no extractable elements
        assert result.success is True
        assert result.function_name == "calculate_area"
        assert len(result.extractable_elements) == 0
    
    def test_show_function_with_comprehensions(self):
        """Test showing a function with list/dict comprehensions (not lambdas)"""
        self.create_file("comprehensions.py", """
def process_numbers(numbers):
    '''Process numbers using various comprehensions'''
    
    # List comprehension
    squares = [x**2 for x in numbers if x > 0]
    
    # Dict comprehension
    number_info = {x: {'square': x**2, 'cube': x**3} for x in numbers}
    
    # Set comprehension
    unique_squares = {x**2 for x in numbers}
    
    # Generator with lambda (this should be detected)
    doubled = list(map(lambda x: x * 2, numbers))
    
    return {
        'squares': squares,
        'info': number_info,
        'unique_squares': unique_squares,
        'doubled': doubled
    }
""")
        
        params = ShowParams(function_name="process_numbers")
        result = self.provider.show_function(params)
        
        # Expected: function found with one lambda (comprehensions not counted)
        assert result.success is True
        assert result.function_name == "process_numbers"
        
        # Should only find the lambda, not comprehensions
        lambda_elements = [e for e in result.extractable_elements if e.type == "lambda"]
        assert len(lambda_elements) == 1
        assert "lambda x: x * 2" in lambda_elements[0].code
    
    def test_show_nonexistent_function(self):
        """Test showing a function that doesn't exist"""
        self.create_file("empty.py", """
def existing_function():
    pass
""")
        
        params = ShowParams(function_name="nonexistent_function")
        result = self.provider.show_function(params)
        
        # Expected: should fail with function not found
        assert result.success is False
        assert result.error_type == "function_not_found"
        assert "nonexistent_function" in result.message
    
    def test_show_class_method_with_lambdas(self):
        """Test showing a class method that contains lambda expressions"""
        self.create_file("calculator.py", """
class StatisticsCalculator:
    def __init__(self):
        self.precision = 4
    
    def calculate_statistics(self, dataset):
        '''Calculate comprehensive statistics for dataset'''
        
        if not dataset:
            return {}
        
        # Filter outliers using lambda
        q1, q3 = self._get_quartiles(dataset)
        iqr = q3 - q1
        filtered_data = list(filter(
            lambda x: q1 - 1.5 * iqr <= x <= q3 + 1.5 * iqr,
            dataset
        ))
        
        # Calculate various metrics using lambdas
        mean = sum(filtered_data) / len(filtered_data)
        variance = sum(map(lambda x: (x - mean) ** 2, filtered_data)) / len(filtered_data)
        std_dev = variance ** 0.5
        
        # Generate percentiles with lambda
        sorted_data = sorted(filtered_data)
        percentiles = {
            p: sorted_data[int(len(sorted_data) * p / 100)]
            for p in [10, 25, 50, 75, 90]
        }
        
        return {
            'mean': round(mean, self.precision),
            'std_dev': round(std_dev, self.precision),
            'variance': round(variance, self.precision),
            'percentiles': percentiles,
            'filtered_count': len(filtered_data),
            'original_count': len(dataset)
        }
    
    def _get_quartiles(self, data):
        sorted_data = sorted(data)
        n = len(sorted_data)
        return sorted_data[n//4], sorted_data[3*n//4]
""")
        
        params = ShowParams(function_name="calculate_statistics")
        result = self.provider.show_function(params)
        
        # Expected: method found with lambda expressions
        assert result.success is True
        assert result.function_name == "calculate_statistics"
        assert len(result.extractable_elements) >= 2  # At least filter and map lambdas
        
        # Verify lambda detection
        lambda_elements = [e for e in result.extractable_elements if e.type == "lambda"]
        assert len(lambda_elements) >= 2
        
        # Check qualified names include class context
        for element in lambda_elements:
            assert "calculate_statistics.lambda_" in element.id
    
    def test_show_function_with_deeply_nested_lambdas(self):
        """Test showing a function with deeply nested lambda expressions"""
        self.create_file("nested_processing.py", """
def complex_data_transformation(raw_data):
    '''Transform data through multiple nested operations'''
    
    # Nested map/filter operations with lambdas
    result = list(map(
        lambda item: {
            **item,
            'processed_values': list(map(
                lambda val: val * 2 if val > 0 else 0,
                item.get('values', [])
            )),
            'filtered_tags': list(filter(
                lambda tag: len(tag) > 2 and tag.isalnum(),
                item.get('tags', [])
            ))
        },
        filter(
            lambda item: item.get('active', False) and len(item.get('values', [])) > 0,
            raw_data
        )
    ))
    
    return result
""")
        
        params = ShowParams(function_name="complex_data_transformation")
        result = self.provider.show_function(params)
        
        # Expected: function found with multiple nested lambdas
        assert result.success is True
        assert result.function_name == "complex_data_transformation"
        assert len(result.extractable_elements) >= 4  # Multiple nested lambdas
        
        # All should be lambda type
        lambda_elements = [e for e in result.extractable_elements if e.type == "lambda"]
        assert len(lambda_elements) >= 4
        
        # Verify they're all extractable
        for element in lambda_elements:
            assert element.extractable is True
            assert element.type == "lambda"