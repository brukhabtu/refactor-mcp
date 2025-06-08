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
    
    def start_operation(self, operation: str, **metadata: Any) -> OperationMetrics:
        """Start tracking an operation."""
        metrics = OperationMetrics(
            operation=operation,
            start_time=time.time(),
            metadata=metadata,
        )
        self.operations.append(metrics)
        logger.debug(f"Started operation: {operation}", extra={"metadata": metadata})
        return metrics
    
    def complete_operation(
        self,
        metrics: OperationMetrics,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Complete an operation."""
        metrics.end_time = time.time()
        metrics.success = success
        metrics.error_message = error_message
        
        log_data = metrics.to_dict()
        if success:
            logger.info(f"Completed operation: {metrics.operation}", extra=log_data)
        else:
            logger.error(
                f"Failed operation: {metrics.operation} - {error_message}",
                extra=log_data,
            )
    
    @contextmanager
    def track_operation(
        self, operation: str, **metadata: Any
    ) -> Generator[OperationMetrics, None, None]:
        """Context manager for tracking operations."""
        metrics = self.start_operation(operation, **metadata)
        try:
            yield metrics
            self.complete_operation(metrics, success=True)
        except Exception as e:
            self.complete_operation(metrics, success=False, error_message=str(e))
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all operations."""
        total_operations = len(self.operations)
        successful_operations = sum(1 for op in self.operations if op.success)
        failed_operations = total_operations - successful_operations
        
        completed_operations = [op for op in self.operations if op.end_time is not None]
        avg_duration = (
            sum(op.duration_ms for op in completed_operations) / len(completed_operations)
            if completed_operations
            else 0
        )
        
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "average_duration_ms": avg_duration,
        }


# Global tracker instance
_tracker = OperationTracker()


def get_tracker() -> OperationTracker:
    """Get the global operation tracker."""
    return _tracker


@contextmanager
def track_operation(operation: str, **metadata: Any) -> Generator[OperationMetrics, None, None]:
    """Track an operation using the global tracker."""
    with _tracker.track_operation(operation, **metadata) as metrics:
        yield metrics