"""
Complex Python module for advanced refactoring testing.

This module contains more complex patterns:
- Nested classes and functions
- Decorators and properties
- Context managers
- Exception handling
- Async/await patterns
- Complex inheritance
"""

import asyncio
import contextlib
import functools
from abc import ABC, abstractmethod
from typing import Generator, AsyncGenerator, Protocol, TypeVar, Generic


T = TypeVar('T')


def timing_decorator(func):
    """Decorator for timing function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper


def validation_decorator(validation_func):
    """Parameterized decorator for input validation."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not validation_func(*args, **kwargs):
                raise ValueError("Validation failed")
            return func(*args, **kwargs)
        return wrapper
    return decorator


class DataProcessor(Protocol):
    """Protocol for data processors."""
    
    def process(self, data: T) -> T:
        """Process data and return result."""
        ...


class BaseProcessor(ABC, Generic[T]):
    """Abstract base class for processors."""
    
    def __init__(self, name: str):
        self.name = name
        self._cache = {}
    
    @abstractmethod
    def _process_impl(self, data: T) -> T:
        """Implementation-specific processing."""
        pass
    
    @timing_decorator
    def process(self, data: T) -> T:
        """Process data with caching."""
        cache_key = str(hash(str(data)))
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = self._process_impl(data)
        self._cache[cache_key] = result
        return result
    
    def clear_cache(self):
        """Clear the processor cache."""
        self._cache.clear()
    
    @property
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class TextProcessor(BaseProcessor[str]):
    """Text processing implementation."""
    
    def __init__(self, name: str, transform_func=None):
        super().__init__(name)
        self.transform_func = transform_func or (lambda x: x.upper())
    
    def _process_impl(self, data: str) -> str:
        """Process text data."""
        # Nested function for extraction testing
        def clean_text(text):
            """Clean input text."""
            return text.strip().replace("\n", " ")
        
        cleaned = clean_text(data)
        
        # Lambda for transformation testing
        apply_transform = lambda text: self.transform_func(text)
        
        return apply_transform(cleaned)
    
    def batch_process(self, texts: list[str]) -> list[str]:
        """Process multiple texts."""
        # Generator expression for extraction testing
        results = (self.process(text) for text in texts if text)
        return list(results)


class NumberProcessor(BaseProcessor[float]):
    """Number processing implementation."""
    
    def __init__(self, name: str, precision: int = 2):
        super().__init__(name)
        self.precision = precision
    
    @validation_decorator(lambda self, data: isinstance(data, (int, float)))
    def _process_impl(self, data: float) -> float:
        """Process numeric data."""
        # Complex calculation for extraction testing
        def calculate_result(value):
            """Perform complex calculation."""
            import math
            
            # Multiple operations that could be extracted
            normalized = value / 100.0
            scaled = normalized * math.pi
            rounded = round(scaled, self.precision)
            
            return rounded
        
        return calculate_result(data)
    
    def statistical_summary(self, numbers: list[float]) -> dict:
        """Calculate statistical summary."""
        if not numbers:
            return {}
        
        # Statistical functions for extraction testing
        mean_calc = lambda values: sum(values) / len(values)
        variance_calc = lambda values, mean: sum((x - mean) ** 2 for x in values) / len(values)
        
        processed = [self.process(num) for num in numbers]
        mean = mean_calc(processed)
        variance = variance_calc(processed, mean)
        
        return {
            "count": len(processed),
            "mean": mean,
            "variance": variance,
            "min": min(processed),
            "max": max(processed)
        }


class ProcessorFactory:
    """Factory for creating processors."""
    
    _processors = {
        "text": TextProcessor,
        "number": NumberProcessor
    }
    
    @classmethod
    def create_processor(cls, processor_type: str, name: str, **kwargs):
        """Create a processor instance."""
        if processor_type not in cls._processors:
            available = ", ".join(cls._processors.keys())
            raise ValueError(f"Unknown processor type: {processor_type}. Available: {available}")
        
        processor_class = cls._processors[processor_type]
        return processor_class(name, **kwargs)
    
    @classmethod
    def register_processor(cls, name: str, processor_class):
        """Register a new processor type."""
        if not issubclass(processor_class, BaseProcessor):
            raise TypeError("Processor must inherit from BaseProcessor")
        
        cls._processors[name] = processor_class


@contextlib.contextmanager
def processor_context(processor: BaseProcessor) -> Generator[BaseProcessor, None, None]:
    """Context manager for processor lifecycle."""
    print(f"Starting processor: {processor.name}")
    try:
        yield processor
    finally:
        processor.clear_cache()
        print(f"Cleaned up processor: {processor.name}")


class AsyncDataProcessor:
    """Async processor for demonstration."""
    
    def __init__(self, delay: float = 0.1):
        self.delay = delay
        self.processed_count = 0
    
    async def process_item(self, item: str) -> str:
        """Process a single item asynchronously."""
        await asyncio.sleep(self.delay)
        
        # Async transformation for testing
        transform = lambda x: f"processed_{x}_{self.processed_count}"
        
        self.processed_count += 1
        return transform(item)
    
    async def process_batch(self, items: list[str]) -> list[str]:
        """Process multiple items concurrently."""
        # Async list comprehension for extraction testing
        tasks = [self.process_item(item) for item in items]
        results = await asyncio.gather(*tasks)
        return results
    
    async def process_stream(self, items: list[str]) -> AsyncGenerator[str, None]:
        """Process items as a stream."""
        for item in items:
            processed = await self.process_item(item)
            yield processed


class ConfigurationManager:
    """Configuration management with nested structure."""
    
    def __init__(self):
        self._config = {}
        self._validators = {}
    
    def set_config(self, key: str, value, validator=None):
        """Set configuration value with optional validation."""
        if validator:
            self._validators[key] = validator
        
        # Validation logic for extraction testing
        def validate_and_set(config_key, config_value, validation_func):
            """Validate and set configuration."""
            if validation_func and not validation_func(config_value):
                raise ValueError(f"Invalid value for {config_key}: {config_value}")
            
            self._config[config_key] = config_value
        
        validate_and_set(key, value, validator)
    
    def get_config(self, key: str, default=None):
        """Get configuration value."""
        return self._config.get(key, default)
    
    def validate_all(self) -> bool:
        """Validate all configuration values."""
        # Validation generator for extraction testing
        validation_results = (
            self._validators[key](self._config[key])
            for key in self._validators
            if key in self._config
        )
        
        return all(validation_results)
    
    class ConfigSection:
        """Nested class for configuration sections."""
        
        def __init__(self, parent, section_name):
            self.parent = parent
            self.section_name = section_name
        
        def set(self, key: str, value):
            """Set value in this section."""
            full_key = f"{self.section_name}.{key}"
            self.parent.set_config(full_key, value)
        
        def get(self, key: str, default=None):
            """Get value from this section."""
            full_key = f"{self.section_name}.{key}"
            return self.parent.get_config(full_key, default)
    
    def section(self, name: str) -> ConfigSection:
        """Get a configuration section."""
        return self.ConfigSection(self, name)


def demonstrate_usage():
    """Demonstrate the usage of various classes."""
    # Text processing example
    text_processor = ProcessorFactory.create_processor(
        "text", 
        "demo_text", 
        transform_func=lambda x: x.title()
    )
    
    with processor_context(text_processor) as proc:
        result = proc.process("hello world from refactor-mcp")
        print(f"Text result: {result}")
    
    # Number processing example
    number_processor = ProcessorFactory.create_processor("number", "demo_numbers", precision=3)
    
    numbers = [10.5, 20.7, 30.9, 40.1]
    summary = number_processor.statistical_summary(numbers)
    print(f"Number summary: {summary}")
    
    # Configuration example
    config = ConfigurationManager()
    
    # Validator functions for testing
    positive_validator = lambda x: isinstance(x, (int, float)) and x > 0
    string_validator = lambda x: isinstance(x, str) and len(x) > 0
    
    config.set_config("max_workers", 10, positive_validator)
    config.set_config("app_name", "RefactorMCP", string_validator)
    
    # Use configuration sections
    db_section = config.section("database")
    db_section.set("host", "localhost")
    db_section.set("port", 5432)
    
    print(f"Config valid: {config.validate_all()}")


async def async_demo():
    """Demonstrate async processing."""
    processor = AsyncDataProcessor(delay=0.05)
    
    items = ["item1", "item2", "item3", "item4"]
    
    # Batch processing
    batch_results = await processor.process_batch(items)
    print(f"Batch results: {batch_results}")
    
    # Stream processing
    stream_results = []
    async for result in processor.process_stream(items):
        stream_results.append(result)
    
    print(f"Stream results: {stream_results}")


if __name__ == "__main__":
    demonstrate_usage()
    
    # Run async demo
    asyncio.run(async_demo())