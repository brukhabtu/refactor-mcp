"""
Mock refactoring provider implementations for testing.

These mock providers simulate the behavior of real refactoring engines
while providing controlled, predictable responses for testing.
"""

from typing import Union, Dict, List, Any
from datetime import datetime

from refactor_mcp.models import (
    SymbolInfo,
    ElementInfo,
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
from refactor_mcp.providers.base import (
    ProviderMetadata,
    OperationCapability,
    ProviderHealthStatus,
)


class MockRopeProvider:
    """
    Mock implementation of a Rope-based refactoring provider.
    
    Provides realistic responses for testing without requiring
    actual Rope library integration.
    """
    
    def __init__(self, project_path: str = "/mock/project"):
        self.name = "mock_rope"
        self.project_path = project_path
        self.supported_languages = ["python"]
        
        # Mock data store for symbols
        self._symbols = {
            "get_user_info": SymbolInfo(
                name="get_user_info",
                qualified_name="sample_module.get_user_info", 
                type="function",
                definition_location="sample_module.py:15",
                scope="global",
                docstring="Get user information by ID."
            ),
            "UserSession": SymbolInfo(
                name="UserSession",
                qualified_name="sample_module.UserSession",
                type="class", 
                definition_location="sample_module.py:45",
                scope="global",
                docstring="User session data class."
            ),
            "process_users": SymbolInfo(
                name="process_users",
                qualified_name="sample_module.process_users",
                type="function",
                definition_location="sample_module.py:30",
                scope="global",
                docstring="Process multiple users."
            ),
            "SessionManager.create_session": SymbolInfo(
                name="create_session",
                qualified_name="sample_module.SessionManager.create_session",
                type="method",
                definition_location="sample_module.py:95",
                scope="class",
                docstring="Create a new user session."
            )
        }
        
        # Mock extractable elements
        self._extractable_elements = {
            "get_user_info": [
                ElementInfo(
                    id="lambda_1",
                    type="lambda",
                    code="lambda x: x > 0 and x < 1000000",
                    location="sample_module.py:20",
                    extractable=True
                ),
                ElementInfo(
                    id="nested_function_1", 
                    type="function",
                    code="def format_user_data(data):",
                    location="sample_module.py:25",
                    extractable=True
                )
            ],
            "process_users": [
                ElementInfo(
                    id="lambda_2",
                    type="lambda", 
                    code="lambda uid: uid > 0",
                    location="sample_module.py:35",
                    extractable=True
                ),
                ElementInfo(
                    id="lambda_3",
                    type="lambda",
                    code="lambda u: u['name']",
                    location="sample_module.py:42",
                    extractable=True
                )
            ]
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if provider supports the given language."""
        return language.lower() in self.supported_languages

    def get_capabilities(self, language: str) -> List[str]:
        """Return list of supported operations for language"""
        if not self.supports_language(language):
            return []
        return ["analyze", "rename", "extract", "find", "show"]
    
    def analyze_symbol(self, params: AnalyzeParams) -> Union[AnalysisResult, ErrorResponse]:
        """Analyze a symbol and return information."""
        symbol_name = params.symbol_name
        
        if symbol_name not in self._symbols:
            return create_error_response(
                "symbol_not_found",
                f"Symbol '{symbol_name}' not found",
                [f"Did you mean '{name}'?" for name in self._symbols.keys() if name.startswith(symbol_name[:3])]
            )
        
        symbol_info = self._symbols[symbol_name]
        
        # Mock reference locations
        references = [
            f"test_{symbol_name}.py:10",
            "main.py:25",
            "utils.py:15"
        ]
        
        return AnalysisResult(
            success=True,
            symbol_info=symbol_info,
            references=references,
            reference_count=len(references),
            refactoring_suggestions=[
                "Consider adding type hints",
                "Could benefit from extraction of complex logic"
            ]
        )
    
    def rename_symbol(self, params: RenameParams) -> Union[RenameResult, ErrorResponse]:
        """Rename a symbol across the codebase."""
        old_name = params.symbol_name
        new_name = params.new_name
        
        if old_name not in self._symbols:
            return create_error_response(
                "symbol_not_found",
                f"Symbol '{old_name}' not found",
                [f"Did you mean '{name}'?" for name in self._symbols.keys()]
            )
        
        # Check for naming conflicts
        if new_name in self._symbols:
            return RenameResult(
                success=False,
                old_name=old_name,
                new_name=new_name,
                qualified_name=f"module.{old_name}",
                conflicts=[f"Symbol '{new_name}' already exists in scope"]
            )
        
        # Simulate successful rename
        symbol_info = self._symbols[old_name]
        files_modified = [
            "sample_module.py",
            "test_sample_module.py",
            "__init__.py"
        ]
        
        return RenameResult(
            success=True,
            old_name=old_name,
            new_name=new_name,
            qualified_name=symbol_info.qualified_name.replace(old_name, new_name),
            files_modified=files_modified,
            references_updated=5,
            backup_id=f"backup_{hash(f'{old_name}_{new_name}')}"
        )
    
    def extract_element(self, params: ExtractParams) -> Union[ExtractResult, ErrorResponse]:
        """Extract an element into a new function."""
        source = params.source
        new_name = params.new_name
        
        # Parse source to get function and element
        if "." not in source:
            return create_error_response(
                "invalid_source",
                f"Invalid source format: '{source}'. Expected 'function.element_id'",
                ["Use format like 'function_name.lambda_1'"]
            )
        
        function_name, element_id = source.split(".", 1)
        
        if function_name not in self._extractable_elements:
            return create_error_response(
                "function_not_found",
                f"Function '{function_name}' not found",
                list(self._extractable_elements.keys())
            )
        
        elements = self._extractable_elements[function_name]
        element = next((e for e in elements if e.id == element_id), None)
        
        if not element:
            available_elements = [e.id for e in elements]
            return create_error_response(
                "element_not_found",
                f"Element '{element_id}' not found in function '{function_name}'",
                available_elements
            )
        
        if not element.extractable:
            return create_error_response(
                "not_extractable",
                f"Element '{element_id}' cannot be extracted",
                ["Element is too simple or has dependencies"]
            )
        
        # Generate extracted code based on element type
        if element.type == "lambda":
            extracted_code = f"def {new_name}(x):\n    return {element.code.split(': ', 1)[1]}"
            parameters = ["x"]
            return_type = "bool"
        else:
            extracted_code = f"def {new_name}():\n    # Extracted function\n    pass"
            parameters = []
            return_type = "None"
        
        return ExtractResult(
            success=True,
            source=source,
            new_function_name=new_name,
            extracted_code=extracted_code,
            parameters=parameters,
            return_type=return_type,
            files_modified=["sample_module.py"],
            backup_id=f"backup_extract_{hash(source)}"
        )
    
    def find_symbols(self, params: FindParams) -> Union[FindResult, ErrorResponse]:
        """Find symbols matching a pattern."""
        pattern = params.pattern.lower()
        matches = []
        
        for symbol_info in self._symbols.values():
            # Simple pattern matching
            if (pattern.replace("*", "") in symbol_info.name.lower() or
                pattern.replace("*", "") in symbol_info.qualified_name.lower()):
                matches.append(symbol_info)
        
        return FindResult(
            success=True,
            pattern=params.pattern,
            matches=matches,
            total_count=len(matches)
        )
    
    def show_function(self, params: ShowParams) -> Union[ShowResult, ErrorResponse]:
        """Show extractable elements in a function."""
        function_name = params.function_name
        
        if function_name not in self._extractable_elements:
            return create_error_response(
                "function_not_found",
                f"Function '{function_name}' not found",
                list(self._extractable_elements.keys())
            )
        
        elements = self._extractable_elements[function_name]
        
        return ShowResult(
            success=True,
            function_name=function_name,
            extractable_elements=elements
        )

    # Enhanced protocol methods
    def get_metadata(self) -> ProviderMetadata:
        """Get provider metadata including name, version, and capabilities"""
        return ProviderMetadata(
            name="mock_rope_provider",
            version="1.0.0",
            description="Mock implementation of Rope-based refactoring provider for testing",
            author="Test Suite",
            supported_languages=self.supported_languages,
            min_protocol_version="1.0.0",
            max_protocol_version="1.0.0"
        )

    def get_detailed_capabilities(self, language: str) -> Dict[str, List[OperationCapability]]:
        """Get detailed capability information organized by operation category"""
        if not self.supports_language(language):
            return {"analysis": [], "refactoring": [], "discovery": []}
        
        return {
            "analysis": [
                OperationCapability(
                    name="analyze_symbol",
                    support_level="full",
                    description="Analyze symbol information and references",
                    limitations=None
                )
            ],
            "refactoring": [
                OperationCapability(
                    name="rename_symbol",
                    support_level="full",
                    description="Safe symbol renaming with conflict detection"
                ),
                OperationCapability(
                    name="extract_element",
                    support_level="partial",
                    description="Extract code elements into new functions",
                    limitations=["Limited to simple expressions", "May not handle complex dependencies"]
                )
            ],
            "discovery": [
                OperationCapability(
                    name="find_symbols",
                    support_level="full",
                    description="Find symbols matching patterns"
                ),
                OperationCapability(
                    name="show_function",
                    support_level="experimental",
                    description="Show extractable elements within functions",
                    limitations=["Basic pattern matching only"]
                )
            ]
        }

    def health_check(self) -> ProviderHealthStatus:
        """Perform health check and return status information"""
        return ProviderHealthStatus(
            status="healthy",
            details={
                "project_path": self.project_path,
                "symbols_loaded": len(self._symbols),
                "extractable_elements": sum(len(elements) for elements in self._extractable_elements.values()),
                "memory_usage": "normal"
            },
            dependencies=["rope", "python-ast"],
            last_check=datetime.now().isoformat()
        )

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate provider configuration and return validation results"""
        return {
            "valid": True,
            "project_path_exists": True,
            "dependencies_available": True,
            "configuration_complete": True,
            "warnings": [],
            "errors": []
        }

    def get_priority(self, language: str) -> int:
        """Get provider priority for language-specific operations (higher = better)"""
        if language.lower() == "python":
            return 90  # High priority for Python
        elif language.lower() in ["javascript", "typescript"]:
            return 20  # Low priority for JS/TS
        else:
            return 0   # No support

    def is_compatible(self, protocol_version: str) -> bool:
        """Check if provider is compatible with given protocol version"""
        # Simple version compatibility - in real implementation would use semver
        supported_versions = ["1.0.0", "1.0.1", "1.1.0"]
        return protocol_version in supported_versions


class MockTreeSitterProvider:
    """
    Mock implementation of a Tree-sitter based provider.
    
    Simulates multi-language support with Tree-sitter parsing.
    """
    
    def __init__(self):
        self.name = "mock_tree_sitter"
        self.supported_languages = ["python", "javascript", "typescript", "rust", "go"]
    
    def supports_language(self, language: str) -> bool:
        """Check if provider supports the given language."""
        return language.lower() in self.supported_languages

    def get_capabilities(self, language: str) -> List[str]:
        """Return list of supported operations for language"""
        if not self.supports_language(language):
            return []
        return ["analyze", "rename", "extract", "find", "show"]
    
    def analyze_symbol(self, params: AnalyzeParams) -> Union[AnalysisResult, ErrorResponse]:
        """Analyze symbol using Tree-sitter parsing."""
        # Simplified implementation for testing
        symbol_info = SymbolInfo(
            name=params.symbol_name,
            qualified_name=f"module.{params.symbol_name}",
            type="function",
            definition_location="module.py:1",
            scope="global"
        )
        
        return AnalysisResult(
            success=True,
            symbol_info=symbol_info,
            references=["module.py:10"],
            reference_count=1,
            refactoring_suggestions=["Tree-sitter based suggestion"]
        )
    
    def rename_symbol(self, params: RenameParams) -> Union[RenameResult, ErrorResponse]:
        """Rename symbol using Tree-sitter."""
        return RenameResult(
            success=True,
            old_name=params.symbol_name,
            new_name=params.new_name,
            qualified_name=f"module.{params.new_name}",
            files_modified=["module.py"],
            references_updated=1,
            backup_id="tree_sitter_backup"
        )
    
    def extract_element(self, params: ExtractParams) -> Union[ExtractResult, ErrorResponse]:
        """Extract element using Tree-sitter."""
        return ExtractResult(
            success=True,
            source=params.source,
            new_function_name=params.new_name,
            extracted_code=f"def {params.new_name}():\n    pass",
            parameters=[],
            return_type="None",
            files_modified=["module.py"],
            backup_id="tree_sitter_extract"
        )
    
    def find_symbols(self, params: FindParams) -> Union[FindResult, ErrorResponse]:
        """Find symbols using Tree-sitter."""
        return FindResult(
            success=True,
            pattern=params.pattern,
            matches=[],
            total_count=0
        )
    
    def show_function(self, params: ShowParams) -> Union[ShowResult, ErrorResponse]:
        """Show function elements using Tree-sitter."""
        return ShowResult(
            success=True,
            function_name=params.function_name,
            extractable_elements=[]
        )

    # Enhanced protocol methods (minimal implementation)
    def get_metadata(self) -> ProviderMetadata:
        """Get provider metadata"""
        return ProviderMetadata(
            name="mock_tree_sitter_provider",
            version="0.9.0",
            description="Mock Tree-sitter based multi-language provider",
            author="Test Suite",
            supported_languages=self.supported_languages
        )

    def get_detailed_capabilities(self, language: str) -> Dict[str, List[OperationCapability]]:
        """Get detailed capabilities"""
        if not self.supports_language(language):
            return {"analysis": [], "refactoring": [], "discovery": []}
        return {
            "analysis": [OperationCapability(name="analyze_symbol", support_level="experimental")],
            "refactoring": [OperationCapability(name="rename_symbol", support_level="experimental")],
            "discovery": [OperationCapability(name="find_symbols", support_level="experimental")]
        }

    def health_check(self) -> ProviderHealthStatus:
        """Health check"""
        return ProviderHealthStatus(status="healthy", details={}, dependencies=["tree-sitter"])

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration"""
        return {"valid": True}

    def get_priority(self, language: str) -> int:
        """Get priority"""
        return 50 if self.supports_language(language) else 0

    def is_compatible(self, protocol_version: str) -> bool:
        """Check compatibility"""
        return protocol_version == "1.0.0"


class FailingProvider:
    """
    Mock provider that always returns errors.
    
    Useful for testing error handling and recovery scenarios.
    """
    
    def __init__(self, error_type: str = "provider_error"):
        self.name = "failing_provider"
        self.error_type = error_type
        self.supported_languages = ["python"]
    
    def supports_language(self, language: str) -> bool:
        """Check language support."""
        return language.lower() in self.supported_languages

    def get_capabilities(self, language: str) -> List[str]:
        """Return empty capabilities (failing provider)"""
        return []
    
    def analyze_symbol(self, params: AnalyzeParams) -> ErrorResponse:
        """Always return an error."""
        return create_error_response(
            self.error_type,
            f"Failed to analyze symbol '{params.symbol_name}'",
            ["Check symbol name", "Verify file exists"]
        )
    
    def rename_symbol(self, params: RenameParams) -> ErrorResponse:
        """Always return an error."""
        return create_error_response(
            self.error_type,
            f"Failed to rename symbol '{params.symbol_name}'",
            ["Check for conflicts", "Verify write permissions"]
        )
    
    def extract_element(self, params: ExtractParams) -> ErrorResponse:
        """Always return an error."""
        return create_error_response(
            self.error_type,
            f"Failed to extract element '{params.source}'",
            ["Check element extractability", "Verify syntax"]
        )
    
    def find_symbols(self, params: FindParams) -> ErrorResponse:
        """Always return an error."""
        return create_error_response(
            self.error_type,
            f"Failed to find symbols matching '{params.pattern}'",
            ["Check pattern syntax", "Verify project structure"]
        )
    
    def show_function(self, params: ShowParams) -> ErrorResponse:
        """Always return an error."""
        return create_error_response(
            self.error_type,
            f"Failed to show function '{params.function_name}'",
            ["Check function exists", "Verify file readable"]
        )


class ConfigurableProvider:
    """
    Configurable mock provider for flexible testing scenarios.
    
    Allows setting up different response patterns for various test cases.
    """
    
    def __init__(self, name: str = "configurable_provider"):
        self.name = name
        self.supported_languages = ["python"]
        
        # Configuration for responses
        self._analyze_responses = {}
        self._rename_responses = {}
        self._extract_responses = {}
        self._find_responses = {}
        self._show_responses = {}
    
    def supports_language(self, language: str) -> bool:
        """Check language support."""
        return language.lower() in self.supported_languages

    def get_capabilities(self, language: str) -> List[str]:
        """Return configurable capabilities"""
        if not self.supports_language(language):
            return []
        return ["analyze", "rename", "extract", "find", "show"]
    
    def configure_analyze_response(self, symbol_name: str, response: Union[AnalysisResult, ErrorResponse]):
        """Configure response for analyze_symbol."""
        self._analyze_responses[symbol_name] = response
    
    def configure_rename_response(self, old_name: str, response: Union[RenameResult, ErrorResponse]):
        """Configure response for rename_symbol."""
        self._rename_responses[old_name] = response
    
    def configure_extract_response(self, source: str, response: Union[ExtractResult, ErrorResponse]):
        """Configure response for extract_element."""
        self._extract_responses[source] = response
    
    def configure_find_response(self, pattern: str, response: Union[FindResult, ErrorResponse]):
        """Configure response for find_symbols."""
        self._find_responses[pattern] = response
    
    def configure_show_response(self, function_name: str, response: Union[ShowResult, ErrorResponse]):
        """Configure response for show_function."""
        self._show_responses[function_name] = response
    
    def analyze_symbol(self, params: AnalyzeParams) -> Union[AnalysisResult, ErrorResponse]:
        """Return configured response or default error."""
        return self._analyze_responses.get(
            params.symbol_name,
            create_error_response("not_configured", f"No response configured for '{params.symbol_name}'")
        )
    
    def rename_symbol(self, params: RenameParams) -> Union[RenameResult, ErrorResponse]:
        """Return configured response or default error."""
        return self._rename_responses.get(
            params.symbol_name,
            create_error_response("not_configured", f"No response configured for '{params.symbol_name}'")
        )
    
    def extract_element(self, params: ExtractParams) -> Union[ExtractResult, ErrorResponse]:
        """Return configured response or default error."""
        return self._extract_responses.get(
            params.source,
            create_error_response("not_configured", f"No response configured for '{params.source}'")
        )
    
    def find_symbols(self, params: FindParams) -> Union[FindResult, ErrorResponse]:
        """Return configured response or default error."""
        return self._find_responses.get(
            params.pattern,
            create_error_response("not_configured", f"No response configured for '{params.pattern}'")
        )
    
    def show_function(self, params: ShowParams) -> Union[ShowResult, ErrorResponse]:
        """Return configured response or default error."""
        return self._show_responses.get(
            params.function_name,
            create_error_response("not_configured", f"No response configured for '{params.function_name}'")
        )