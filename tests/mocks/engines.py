"""
Mock refactoring engine implementations for testing.

Provides mock engines that simulate the behavior of the main
RefactoringEngine without requiring real provider implementations.
"""

from typing import List, Dict, Any, Optional, Union

from refactor_mcp.models import (
    AnalysisResult,
    RenameResult,
    ExtractResult,
    FindResult,
    ShowResult,
    ErrorResponse,
    create_error_response,
    AnalyzeParams,
    RenameParams,
    ExtractParams,
    FindParams,
    ShowParams,
)
from .providers import MockRopeProvider, MockTreeSitterProvider, FailingProvider


class MockRefactoringEngine:
    """
    Mock implementation of the main RefactoringEngine.
    
    Provides a simplified engine for testing that manages
    mock providers and routes operations.
    """
    
    def __init__(self):
        self.providers = {}
        self.default_provider = None
        self.operation_history = []
        
        # Add default mock providers
        self.register_provider(MockRopeProvider())
        self.register_provider(MockTreeSitterProvider())
        
        # Set rope as default
        self.set_default_provider("mock_rope")
    
    def register_provider(self, provider) -> None:
        """Register a refactoring provider."""
        self.providers[provider.name] = provider
    
    def unregister_provider(self, provider_name: str) -> bool:
        """Unregister a provider."""
        if provider_name in self.providers:
            del self.providers[provider_name]
            if self.default_provider == provider_name:
                self.default_provider = None
            return True
        return False
    
    def set_default_provider(self, provider_name: str) -> bool:
        """Set the default provider."""
        if provider_name in self.providers:
            self.default_provider = provider_name
            return True
        return False
    
    def get_provider(self, provider_name: str = None):
        """Get a provider by name or return default."""
        if provider_name:
            return self.providers.get(provider_name)
        
        if self.default_provider:
            return self.providers.get(self.default_provider)
        
        # Return first available provider
        if self.providers:
            return next(iter(self.providers.values()))
        
        return None
    
    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self.providers.keys())
    
    def supports_language(self, language: str, provider_name: str = None) -> bool:
        """Check if a provider supports the given language."""
        provider = self.get_provider(provider_name)
        if provider:
            return provider.supports_language(language)
        return False
    
    def analyze_symbol(self, params: AnalyzeParams, provider_name: str = None) -> Union[AnalysisResult, ErrorResponse]:
        """Analyze a symbol using the specified or default provider."""
        self.operation_history.append(("analyze", params.symbol_name, provider_name))
        
        provider = self.get_provider(provider_name)
        if not provider:
            return create_error_response(
                "no_provider",
                "No suitable provider available",
                self.list_providers()
            )
        
        return provider.analyze_symbol(params)
    
    def rename_symbol(self, params: RenameParams, provider_name: str = None) -> Union[RenameResult, ErrorResponse]:
        """Rename a symbol using the specified or default provider."""
        self.operation_history.append(("rename", f"{params.symbol_name}->{params.new_name}", provider_name))
        
        provider = self.get_provider(provider_name)
        if not provider:
            return create_error_response(
                "no_provider",
                "No suitable provider available",
                self.list_providers()
            )
        
        return provider.rename_symbol(params)
    
    def extract_element(self, params: ExtractParams, provider_name: str = None) -> Union[ExtractResult, ErrorResponse]:
        """Extract an element using the specified or default provider."""
        self.operation_history.append(("extract", f"{params.source}->{params.new_name}", provider_name))
        
        provider = self.get_provider(provider_name)
        if not provider:
            return create_error_response(
                "no_provider",
                "No suitable provider available",
                self.list_providers()
            )
        
        return provider.extract_element(params)
    
    def find_symbols(self, params: FindParams, provider_name: str = None) -> Union[FindResult, ErrorResponse]:
        """Find symbols using the specified or default provider."""
        self.operation_history.append(("find", params.pattern, provider_name))
        
        provider = self.get_provider(provider_name)
        if not provider:
            return create_error_response(
                "no_provider",
                "No suitable provider available",
                self.list_providers()
            )
        
        return provider.find_symbols(params)
    
    def show_function(self, params: ShowParams, provider_name: str = None) -> Union[ShowResult, ErrorResponse]:
        """Show function elements using the specified or default provider."""
        self.operation_history.append(("show", params.function_name, provider_name))
        
        provider = self.get_provider(provider_name)
        if not provider:
            return create_error_response(
                "no_provider", 
                "No suitable provider available",
                self.list_providers()
            )
        
        return provider.show_function(params)
    
    def get_operation_history(self) -> List[tuple]:
        """Get the history of operations performed."""
        return self.operation_history.copy()
    
    def clear_operation_history(self) -> None:
        """Clear the operation history."""
        self.operation_history.clear()
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about providers and operations."""
        provider_usage = {}
        operation_counts = {}
        
        for operation, target, provider_used in self.operation_history:
            # Count operations by type
            operation_counts[operation] = operation_counts.get(operation, 0) + 1
            
            # Count usage by provider
            provider_key = provider_used or self.default_provider or "unknown"
            if provider_key not in provider_usage:
                provider_usage[provider_key] = 0
            provider_usage[provider_key] += 1
        
        return {
            "total_operations": len(self.operation_history),
            "registered_providers": len(self.providers),
            "default_provider": self.default_provider,
            "operation_counts": operation_counts,
            "provider_usage": provider_usage,
            "available_providers": self.list_providers()
        }


class MockEngineBuilder:
    """
    Builder for creating configured mock engines.
    
    Provides a fluent interface for setting up test scenarios.
    """
    
    def __init__(self):
        self.engine = MockRefactoringEngine()
        self._clear_default_providers()
    
    def _clear_default_providers(self):
        """Clear default providers for clean setup."""
        for provider_name in list(self.engine.providers.keys()):
            self.engine.unregister_provider(provider_name)
        self.engine.default_provider = None
    
    def with_rope_provider(self, project_path: str = "/mock/project") -> "MockEngineBuilder":
        """Add a rope provider to the engine."""
        provider = MockRopeProvider(project_path)
        self.engine.register_provider(provider)
        return self
    
    def with_tree_sitter_provider(self) -> "MockEngineBuilder":
        """Add a tree-sitter provider to the engine."""
        provider = MockTreeSitterProvider()
        self.engine.register_provider(provider)
        return self
    
    def with_failing_provider(self, error_type: str = "provider_error") -> "MockEngineBuilder":
        """Add a failing provider to the engine."""
        provider = FailingProvider(error_type)
        self.engine.register_provider(provider)
        return self
    
    def with_custom_provider(self, provider) -> "MockEngineBuilder":
        """Add a custom provider to the engine."""
        self.engine.register_provider(provider)
        return self
    
    def with_default_provider(self, provider_name: str) -> "MockEngineBuilder":
        """Set the default provider."""
        self.engine.set_default_provider(provider_name)
        return self
    
    def build(self) -> MockRefactoringEngine:
        """Build the configured engine."""
        return self.engine


class MockOperationTracker:
    """
    Mock implementation of operation tracking for testing.
    
    Simulates the behavior of the actual operation tracker
    without requiring real file system operations.
    """
    
    def __init__(self):
        self.operations = []
        self.current_operation = None
        self.is_tracking = False
    
    def start_operation(self, operation_type: str, details: Dict[str, Any] = None) -> str:
        """Start tracking an operation."""
        operation_id = f"op_{len(self.operations) + 1}"
        
        operation = {
            "id": operation_id,
            "type": operation_type,
            "details": details or {},
            "started_at": "2024-01-01T12:00:00Z",
            "completed_at": None,
            "status": "in_progress",
            "files_affected": [],
            "errors": []
        }
        
        self.operations.append(operation)
        self.current_operation = operation_id
        self.is_tracking = True
        
        return operation_id
    
    def add_file_change(self, file_path: str, change_type: str = "modified") -> None:
        """Record a file change for the current operation."""
        if self.current_operation:
            operation = self._get_operation(self.current_operation)
            if operation:
                operation["files_affected"].append({
                    "path": file_path,
                    "change_type": change_type,
                    "timestamp": "2024-01-01T12:00:01Z"
                })
    
    def add_error(self, error_message: str, error_type: str = "operation_error") -> None:
        """Record an error for the current operation."""
        if self.current_operation:
            operation = self._get_operation(self.current_operation)
            if operation:
                operation["errors"].append({
                    "type": error_type,
                    "message": error_message,
                    "timestamp": "2024-01-01T12:00:02Z"
                })
    
    def complete_operation(self, success: bool = True) -> Optional[Dict[str, Any]]:
        """Complete the current operation."""
        if not self.current_operation:
            return None
        
        operation = self._get_operation(self.current_operation)
        if operation:
            operation["completed_at"] = "2024-01-01T12:00:03Z"
            operation["status"] = "completed" if success else "failed"
        
        self.current_operation = None
        self.is_tracking = False
        
        return operation
    
    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation details by ID."""
        return self._get_operation(operation_id)
    
    def get_all_operations(self) -> List[Dict[str, Any]]:
        """Get all tracked operations."""
        return self.operations.copy()
    
    def get_current_operation(self) -> Optional[Dict[str, Any]]:
        """Get the current operation if any."""
        if self.current_operation:
            return self._get_operation(self.current_operation)
        return None
    
    def clear_history(self) -> None:
        """Clear all operation history."""
        self.operations.clear()
        self.current_operation = None
        self.is_tracking = False
    
    def _get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation by ID."""
        for operation in self.operations:
            if operation["id"] == operation_id:
                return operation
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about tracked operations."""
        total_operations = len(self.operations)
        completed_operations = sum(1 for op in self.operations if op["status"] == "completed")
        failed_operations = sum(1 for op in self.operations if op["status"] == "failed")
        
        operation_types = {}
        for operation in self.operations:
            op_type = operation["type"]
            operation_types[op_type] = operation_types.get(op_type, 0) + 1
        
        total_files_affected = sum(len(op["files_affected"]) for op in self.operations)
        total_errors = sum(len(op["errors"]) for op in self.operations)
        
        return {
            "total_operations": total_operations,
            "completed_operations": completed_operations,
            "failed_operations": failed_operations,
            "in_progress_operations": total_operations - completed_operations - failed_operations,
            "operation_types": operation_types,
            "total_files_affected": total_files_affected,
            "total_errors": total_errors,
            "current_operation": self.current_operation
        }