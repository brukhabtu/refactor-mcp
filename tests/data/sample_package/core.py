"""
Core module for the sample package.

Contains main classes and functions for refactoring testing.
"""

from typing import List, Dict, Any, Optional
from .utils import helper_function, validate_input
from .exceptions import ValidationError, ProcessingError


class DataManager:
    """Main data management class."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.data_store: Dict[str, Any] = {}
        self.processors: List[str] = []
    
    def add_data(self, key: str, value: Any) -> bool:
        """Add data to the manager."""
        if len(self.data_store) >= self.max_size:
            raise ValidationError("Data store is full")
        
        # Validation lambda for extraction testing
        is_valid_key = lambda k: isinstance(k, str) and len(k) > 0
        
        if not is_valid_key(key):
            raise ValidationError("Invalid key format")
        
        self.data_store[key] = value
        return True
    
    def get_data(self, key: str) -> Optional[Any]:
        """Get data from the manager."""
        return self.data_store.get(key)
    
    def remove_data(self, key: str) -> bool:
        """Remove data from the manager."""
        if key in self.data_store:
            del self.data_store[key]
            return True
        return False
    
    def process_all_data(self) -> Dict[str, Any]:
        """Process all stored data."""
        results = {}
        
        # Processing function for extraction testing
        def process_item(key, value):
            """Process individual data item."""
            processed_value = helper_function(value)
            return f"processed_{processed_value}"
        
        for key, value in self.data_store.items():
            try:
                results[key] = process_item(key, value)
            except Exception as e:
                results[key] = f"error: {e}"
        
        return results
    
    def filter_data(self, filter_func) -> Dict[str, Any]:
        """Filter data using provided function."""
        # Filter logic for extraction testing
        filtered_items = {
            key: value for key, value in self.data_store.items()
            if filter_func(key, value)
        }
        return filtered_items


class ProcessingEngine:
    """Engine for processing operations."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.processing_history: List[str] = []
    
    def register_processor(self, processor_name: str) -> None:
        """Register a new processor."""
        if processor_name not in self.data_manager.processors:
            self.data_manager.processors.append(processor_name)
    
    def execute_processing(self, operation: str, **kwargs) -> Any:
        """Execute a processing operation."""
        self.processing_history.append(operation)
        
        # Operation mapping for extraction testing
        operations = {
            "validate": lambda: self._validate_all_data(),
            "transform": lambda: self._transform_data(kwargs.get("transform_func")),
            "aggregate": lambda: self._aggregate_data(kwargs.get("agg_func")),
            "filter": lambda: self._filter_data(kwargs.get("filter_func"))
        }
        
        if operation not in operations:
            raise ProcessingError(f"Unknown operation: {operation}")
        
        try:
            return operations[operation]()
        except Exception as e:
            raise ProcessingError(f"Operation failed: {e}")
    
    def _validate_all_data(self) -> bool:
        """Validate all data in the manager."""
        # Validation generator for extraction testing
        validation_results = (
            validate_input(value) for value in self.data_manager.data_store.values()
        )
        return all(validation_results)
    
    def _transform_data(self, transform_func) -> Dict[str, Any]:
        """Transform all data using provided function."""
        if not transform_func:
            transform_func = lambda x: str(x).upper()
        
        transformed = {}
        for key, value in self.data_manager.data_store.items():
            try:
                transformed[key] = transform_func(value)
            except Exception:
                transformed[key] = value  # Keep original on error
        
        return transformed
    
    def _aggregate_data(self, agg_func) -> Any:
        """Aggregate all data using provided function."""
        if not agg_func:
            # Default aggregation for extraction testing
            agg_func = lambda values: {
                "count": len(values),
                "types": list(set(type(v).__name__ for v in values))
            }
        
        values = list(self.data_manager.data_store.values())
        return agg_func(values)
    
    def _filter_data(self, filter_func) -> Dict[str, Any]:
        """Filter data using provided function."""
        if not filter_func:
            # Default filter for extraction testing
            filter_func = lambda k, v: v is not None
        
        return self.data_manager.filter_data(filter_func)
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of processing operations."""
        # Summary calculation for extraction testing
        operation_counts = {}
        for op in self.processing_history:
            operation_counts[op] = operation_counts.get(op, 0) + 1
        
        return {
            "total_operations": len(self.processing_history),
            "unique_operations": len(set(self.processing_history)),
            "operation_counts": operation_counts,
            "last_operation": self.processing_history[-1] if self.processing_history else None
        }


def create_default_setup() -> tuple[DataManager, ProcessingEngine]:
    """Create default data manager and processing engine setup."""
    # Factory function for extraction testing
    def initialize_manager():
        """Initialize data manager with default settings."""
        manager = DataManager(max_size=500)
        
        # Add some default data
        default_data = {
            "config": {"debug": True, "version": "1.0"},
            "users": ["admin", "user1", "user2"],
            "settings": {"theme": "dark", "language": "en"}
        }
        
        for key, value in default_data.items():
            manager.add_data(key, value)
        
        return manager
    
    manager = initialize_manager()
    engine = ProcessingEngine(manager)
    
    # Register default processors
    default_processors = ["validator", "transformer", "aggregator"]
    for processor in default_processors:
        engine.register_processor(processor)
    
    return manager, engine