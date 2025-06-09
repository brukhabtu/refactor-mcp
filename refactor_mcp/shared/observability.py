"""Observability and metrics for refactor-mcp operations."""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional

from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a refactoring operation."""
    
    operation: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class OperationTracker:
    """Tracks refactoring operations for observability."""
    
    def __init__(self) -> None:
        self.operations: List[OperationMetrics] = []
    
    @contextmanager
    def track_operation(
        self, operation: str, **metadata: Any
    ) -> Generator[OperationMetrics, None, None]:
        """Context manager for tracking operations."""
        metrics = OperationMetrics(
            operation=operation,
            start_time=time.time(),
            metadata=metadata,
        )
        self.operations.append(metrics)
        logger.debug(f"Started operation: {operation}", extra={"metadata": metadata})
        
        try:
            yield metrics
            metrics.end_time = time.time()
            metrics.success = True
            logger.info(f"Completed operation: {operation}", extra=metrics.to_dict())
        except Exception as e:
            metrics.end_time = time.time()
            metrics.success = False
            metrics.error_message = str(e)
            logger.error(f"Failed operation: {operation} - {str(e)}", extra=metrics.to_dict())
            raise


# Global tracker instance
_tracker = OperationTracker()


@contextmanager
def track_operation(operation: str, **metadata: Any) -> Generator[OperationMetrics, None, None]:
    """Track an operation using the global tracker."""
    with _tracker.track_operation(operation, **metadata) as metrics:
        yield metrics