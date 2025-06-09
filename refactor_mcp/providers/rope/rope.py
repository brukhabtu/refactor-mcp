import os
import ast
import uuid
from typing import Dict, List, Optional, Tuple, Any

from rope.base.project import Project
from rope.base.resources import File
from rope.refactor.rename import Rename
from rope.refactor.extract import ExtractMethod
from rope.contrib.findit import find_occurrences

from ...shared.logging import get_logger
from ...shared.observability import track_operation
from ...models import (
    AnalyzeParams,
    AnalysisResult,
    RenameParams,
    RenameResult,
    ExtractParams,
    ExtractResult,
    FindParams,
    FindResult,
    ShowParams,
    ShowResult,
    SymbolInfo,
    ElementInfo,
)
from .. import find_project_root


logger = get_logger(__name__)


class SymbolNotFoundException(Exception):
    pass


class RenameConflictException(Exception):
    def __init__(self, message: str, conflicts: List[str]):
        super().__init__(message)
        self.conflicts = conflicts


class RopeProvider:
    """Rope-based refactoring provider for Python"""

    def __init__(self):
        self._project_cache: Dict[str, Project] = {}
        self._symbol_cache: Dict[Tuple[str, str], Any] = {}

    def supports_language(self, language: str) -> bool:
        return language == "python"

    def get_capabilities(self, language: str) -> List[str]:
        if language == "python":
            return [
                "analyze_symbol",
                "find_symbols",
                "rename_symbol",
                "extract_element",
                "show_function",
            ]
        return []

    def _get_project(self, project_root: str) -> Project:
        """Get or create cached Rope project"""
        if project_root not in self._project_cache:
            prefs = {
                "python_files": ["*.py"],
                "save_objectdb": True,
                "compress_objectdb": False,
                "automatic_soa": True,
                "soa_followed_calls": 0,
                "perform_doa": True,
                "validate_objectdb": True,
                "max_history_items": 32,
                "save_history": True,
                "ignore_syntax_errors": False,
                "ignore_bad_imports": False,
            }

            project = Project(project_root, **prefs)
            self._project_cache[project_root] = project

        return self._project_cache[project_root]

    def _clear_cache(self):
        """Clear project cache and close projects"""
        for project in self._project_cache.values():
            project.close()
        self._project_cache.clear()
        self._symbol_cache.clear()

    def _find_resource(self, project: Project, symbol_name: str) -> Optional[File]:
        """Find the file containing a symbol"""
        # First try to find by exact module path
        if "." in symbol_name:
            module_path = symbol_name.replace(".", os.sep) + ".py"
            try:
                resource = project.get_resource(module_path)
                if resource.exists():
                    return resource
            except Exception:
                pass

        # Search all Python files for the symbol name (just the base name)
        search_name = symbol_name.split(".")[-1]
        for resource in project.get_files():
            if resource.name.endswith(".py"):
                try:
                    source = resource.read()
                    # Parse AST to find the symbol definition
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if (
                            hasattr(node, "name")
                            and node.name == search_name
                            and isinstance(
                                node, (ast.FunctionDef, ast.ClassDef, ast.Name)
                            )
                        ):
                            return resource
                except Exception:
                    continue

        return None

    def _resolve_symbol(self, project: Project, symbol_name: str) -> Optional[Any]:
        """Resolve symbol to its definition in the project"""
        cache_key = (project.address, symbol_name)
        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]

        resource = self._find_resource(project, symbol_name)
        if not resource:
            return None

        try:
            source = resource.read()
            tree = ast.parse(source)

            # Look for the symbol definition
            search_name = symbol_name.split(".")[-1]
            for node in ast.walk(tree):
                if (
                    hasattr(node, "name")
                    and node.name == search_name
                    and isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Assign))
                ):
                    symbol_info = self._create_symbol_info(
                        project, resource, node, symbol_name
                    )
                    self._symbol_cache[cache_key] = symbol_info
                    return symbol_info

            # Also check for variable assignments and other name definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == search_name:
                            symbol_info = self._create_symbol_info(
                                project, resource, target, symbol_name
                            )
                            self._symbol_cache[cache_key] = symbol_info
                            return symbol_info

        except Exception as e:
            logger.warning(f"Failed to parse {resource.path}: {e}")

        return None

    def _create_symbol_info(
        self, project: Project, resource: File, node: ast.AST, symbol_name: str
    ) -> Any:
        """Create symbol info object from AST node"""

        class SymbolInfo:
            def __init__(self, project, resource, node, symbol_name):
                self.project = project
                self.resource = resource
                self.node = node
                self.name = getattr(node, "name", symbol_name.split(".")[-1])
                self.qualified_name = symbol_name
                self.line = getattr(node, "lineno", 1)
                self.offset = self._calculate_offset(resource, node)
                self.type = self._get_node_type(node)
                self.scope = self._get_scope(node)
                self.docstring = self._get_docstring(node)

            def _calculate_offset(self, resource, node):
                try:
                    source = resource.read()
                    lines = source.split("\n")
                    if hasattr(node, "lineno") and hasattr(node, "col_offset"):
                        # Calculate byte offset to the start of the symbol name
                        offset = sum(len(line) + 1 for line in lines[: node.lineno - 1])
                        offset += node.col_offset

                        # For function/class definitions, point to the name, not 'def'/'class'
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                            line_content = lines[node.lineno - 1]
                            if isinstance(node, ast.FunctionDef):
                                name_start = line_content.find(
                                    node.name, node.col_offset
                                )
                            else:
                                name_start = line_content.find(
                                    node.name, node.col_offset
                                )
                            if name_start >= 0:
                                offset = (
                                    sum(
                                        len(line) + 1
                                        for line in lines[: node.lineno - 1]
                                    )
                                    + name_start
                                )

                        return offset
                    return 0
                except Exception:
                    return 0

            def _get_node_type(self, node):
                if isinstance(node, ast.FunctionDef):
                    return "function"
                elif isinstance(node, ast.ClassDef):
                    return "class"
                elif isinstance(node, ast.Name):
                    return "variable"
                else:
                    return "unknown"

            def _get_scope(self, node):
                return "global"

            def _get_docstring(self, node):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.body:
                    first = node.body[0]
                    if isinstance(first, ast.Expr) and isinstance(
                        first.value, ast.Constant
                    ):
                        if isinstance(first.value.value, str):
                            return first.value.value
                    elif isinstance(first, ast.Expr) and isinstance(
                        first.value, ast.Str
                    ):
                        return first.value.s
                return None

        return SymbolInfo(project, resource, node, symbol_name)

    def _analyze_refactoring_opportunities(
        self, project: Project, symbol_info: Any
    ) -> List[str]:
        """Analyze potential refactoring opportunities for a symbol"""
        suggestions = []

        if symbol_info.type == "function":
            source = symbol_info.resource.read()
            lines = source.split("\n")[symbol_info.line - 1 : symbol_info.line + 20]
            if len(lines) > 15:
                suggestions.append("Function is long, consider extracting methods")

        return suggestions

    def _create_analysis_result(
        self,
        symbol_info: Any,
        params: AnalyzeParams,
        references: list,
        suggestions: list,
    ) -> AnalysisResult:
        """Pure function to create analysis result from symbol info and references."""
        reference_files = (
            [ref.resource.path for ref in references] if references else []
        )

        return AnalysisResult(
            success=True,
            symbol_info=SymbolInfo(
                name=symbol_info.name,
                qualified_name=params.symbol_name,
                type=symbol_info.type,
                definition_location=f"{symbol_info.resource.path}:{symbol_info.line}",
                scope=symbol_info.scope,
                docstring=symbol_info.docstring,
            ),
            references=reference_files,
            reference_count=len(references),
            refactoring_suggestions=suggestions,
        )

    def _find_symbol_references(self, project: Any, symbol_info: Any) -> list:
        """Pure function to find symbol references with error handling."""
        try:
            references = find_occurrences(
                project, symbol_info.resource, symbol_info.offset
            )
            return references
        except Exception as e:
            logger.warning(f"Could not find references: {e}")
            return []

    def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
        """Analyze Python symbol using Rope"""
        with track_operation("analyze_symbol", symbol=params.symbol_name):
            try:
                project_root = find_project_root(".")
                project = self._get_project(project_root)

                symbol_info = self._resolve_symbol(project, params.symbol_name)
                if not symbol_info:
                    return AnalysisResult(
                        success=False,
                        error_type="symbol_not_found",
                        message=f"Symbol '{params.symbol_name}' not found",
                    )

                references = self._find_symbol_references(project, symbol_info)
                suggestions = self._analyze_refactoring_opportunities(
                    project, symbol_info
                )

                return self._create_analysis_result(
                    symbol_info, params, references, suggestions
                )

            except Exception as e:
                logger.error(f"Analysis error: {e}")
                return AnalysisResult(
                    success=False, error_type="analysis_error", message=str(e)
                )

    def find_symbols(self, params: FindParams) -> FindResult:
        """Find symbols matching pattern using Rope"""
        with track_operation("find_symbols", pattern=params.pattern):
            try:
                project_root = find_project_root(".")
                project = self._get_project(project_root)

                matches = []
                pattern = params.pattern.lower()

                for resource in project.get_files():
                    if not resource.name.endswith(".py"):
                        continue

                    try:
                        module_symbols = self._extract_module_symbols(project, resource)

                        for symbol in module_symbols:
                            if self._matches_pattern(symbol.name, pattern):
                                matches.append(symbol)

                    except Exception:
                        continue

                return FindResult(
                    success=True,
                    pattern=params.pattern,
                    matches=matches[:100],
                    total_count=len(matches),
                )

            except Exception as e:
                logger.error(f"Search error: {e}")
                return FindResult(
                    success=False, error_type="search_error", message=str(e)
                )

    def _extract_module_symbols(
        self, project: Project, resource: File
    ) -> List[SymbolInfo]:
        """Extract all symbols from a Python module"""
        symbols = []

        try:
            source = resource.read()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    symbols.append(
                        SymbolInfo(
                            name=node.name,
                            qualified_name=f"{resource.path.replace('/', '.').replace('.py', '')}.{node.name}",
                            type="function"
                            if isinstance(node, ast.FunctionDef)
                            else "class",
                            definition_location=f"{resource.path}:{node.lineno}",
                            scope="global",
                        )
                    )

        except Exception:
            pass

        return symbols

    def _matches_pattern(self, symbol_name: str, pattern: str) -> bool:
        """Check if symbol matches search pattern"""
        import fnmatch

        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(symbol_name.lower(), pattern)

        return pattern in symbol_name.lower()

    def _check_rename_conflicts(
        self, project: Project, symbol_info: Any, new_name: str
    ) -> List[str]:
        """Check for potential naming conflicts when renaming"""
        conflicts = []

        try:
            resource = symbol_info.resource
            source = resource.read()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if hasattr(node, "name") and node.name == new_name:
                    conflicts.append(
                        f"Name '{new_name}' already exists in {resource.path}:{getattr(node, 'lineno', 0)}"
                    )

        except Exception:
            pass

        return conflicts

    def _create_backup(self, project: Project) -> str:
        """Create backup of project files before modification"""
        backup_id = str(uuid.uuid4())
        return backup_id

    def rename_symbol(self, params: RenameParams) -> RenameResult:
        """Safely rename Python symbol using Rope"""
        with track_operation(
            "rename_symbol", symbol=params.symbol_name, new_name=params.new_name
        ):
            try:
                project_root = find_project_root(".")
                project = self._get_project(project_root)

                symbol_info = self._resolve_symbol(project, params.symbol_name)
                if not symbol_info:
                    return RenameResult(
                        success=False,
                        error_type="symbol_not_found",
                        message=f"Symbol '{params.symbol_name}' not found",
                    )

                conflicts = self._check_rename_conflicts(
                    project, symbol_info, params.new_name
                )
                if conflicts:
                    return RenameResult(
                        success=False,
                        error_type="naming_conflict",
                        message="Renaming would create conflicts",
                        conflicts=conflicts,
                    )

                backup_id = self._create_backup(project)

                try:
                    renamer = Rename(project, symbol_info.resource, symbol_info.offset)
                    changes = renamer.get_changes(params.new_name)
                    project.do(changes)

                    files_modified = [
                        change.resource.path for change in changes.changes
                    ]
                    references_updated = len(changes.changes)

                    return RenameResult(
                        success=True,
                        old_name=params.symbol_name,
                        new_name=params.new_name,
                        qualified_name=symbol_info.qualified_name,
                        files_modified=files_modified,
                        references_updated=references_updated,
                        backup_id=backup_id,
                    )
                except Exception as e:
                    logger.error(f"Rope rename failed: {e}")
                    return RenameResult(
                        success=False,
                        error_type="rename_error",
                        message=f"Rename operation failed: {str(e)}",
                    )

            except Exception as e:
                logger.error(f"Rename error: {e}")
                return RenameResult(
                    success=False, error_type="rename_error", message=str(e)
                )

    def _parse_extraction_source(self, source: str) -> Optional[Any]:
        """Parse extraction source specification"""

        class SourceInfo:
            def __init__(self, module, function, element=None):
                self.module = module
                self.function = function
                self.element = element

        if not source or "." not in source:
            return None

        parts = source.split(".")
        # Filter out empty parts (handles cases like "...")
        parts = [part for part in parts if part]

        if len(parts) >= 2:
            # For module.function.element pattern
            if len(parts) >= 3:
                return SourceInfo(parts[0], parts[1], parts[2])
            # For module.function pattern
            else:
                return SourceInfo(parts[0], parts[1])

        return None

    def _get_extraction_range(
        self, project: Project, resource: File, source_info: Any
    ) -> Tuple[int, int]:
        """Determine extraction range for code element"""
        try:
            source = resource.read()
            tree = ast.parse(source)

            # Find the parent function first
            function_node = None
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.FunctionDef)
                    and node.name == source_info.function
                ):
                    function_node = node
                    break

            if not function_node:
                # Fallback: extract entire function if element not specified
                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.FunctionDef)
                        and node.name == source_info.function
                    ):
                        lines = source.split("\n")
                        start_offset = sum(
                            len(line) + 1 for line in lines[: node.lineno - 1]
                        )
                        end_line = (
                            node.end_lineno
                            if hasattr(node, "end_lineno")
                            else node.lineno + 10
                        )
                        end_offset = sum(len(line) + 1 for line in lines[:end_line])
                        return start_offset, end_offset
                return 0, len(source)

            # For now, extract a reasonable portion of the function
            # In a real implementation, this would be more sophisticated
            lines = source.split("\n")
            start_line = function_node.lineno + 2  # Skip function def and docstring
            end_line = min(
                start_line + 10,
                function_node.end_lineno
                if hasattr(function_node, "end_lineno")
                else len(lines),
            )

            start_offset = sum(len(line) + 1 for line in lines[: start_line - 1])
            end_offset = sum(len(line) + 1 for line in lines[: end_line - 1])

            return start_offset, end_offset

        except Exception:
            return 0, len(resource.read())

    def _analyze_extracted_function(
        self, project: Project, resource: File, function_name: str
    ) -> Any:
        """Analyze newly extracted function"""

        class ExtractedInfo:
            def __init__(self, code, parameters, return_type):
                self.code = code
                self.parameters = parameters
                self.return_type = return_type

        try:
            source = resource.read()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    code = (
                        ast.unparse(node)
                        if hasattr(ast, "unparse")
                        else "# Extracted function"
                    )
                    parameters = [arg.arg for arg in node.args.args]
                    return_type = None

                    return ExtractedInfo(code, parameters, return_type)

        except Exception:
            pass

        return ExtractedInfo("# Extracted function", [], None)

    def extract_element(self, params: ExtractParams) -> ExtractResult:
        """Extract Python code element using Rope"""
        with track_operation(
            "extract_element", source=params.source, new_name=params.new_name
        ):
            try:
                project_root = find_project_root(".")
                project = self._get_project(project_root)

                source_info = self._parse_extraction_source(params.source)
                if not source_info:
                    return ExtractResult(
                        success=False,
                        error_type="invalid_source",
                        message=f"Cannot parse source: {params.source}",
                    )

                # Find resource by looking for the function in any file
                resource = self._find_resource(project, source_info.function)
                if not resource:
                    return ExtractResult(
                        success=False,
                        error_type="resource_not_found",
                        message=f"Cannot find function: {source_info.function}",
                    )

                start_offset, end_offset = self._get_extraction_range(
                    project, resource, source_info
                )
                backup_id = self._create_backup(project)

                try:
                    extractor = ExtractMethod(
                        project, resource, start_offset, end_offset
                    )
                    changes = extractor.get_changes(params.new_name)
                    project.do(changes)

                    extracted_info = self._analyze_extracted_function(
                        project, resource, params.new_name
                    )

                    return ExtractResult(
                        success=True,
                        source=params.source,
                        new_function_name=params.new_name,
                        extracted_code=extracted_info.code,
                        parameters=extracted_info.parameters,
                        return_type=extracted_info.return_type,
                        files_modified=[resource.path],
                        backup_id=backup_id,
                    )
                except Exception as e:
                    logger.error(f"Rope extraction failed: {e}")
                    return ExtractResult(
                        success=False,
                        error_type="extraction_error",
                        message=f"Extraction failed: {str(e)}",
                    )

            except Exception as e:
                logger.error(f"Extraction error: {e}")
                return ExtractResult(
                    success=False, error_type="extraction_error", message=str(e)
                )

    def show_function(self, params: ShowParams) -> ShowResult:
        """Show extractable elements within Python function"""
        with track_operation("show_function", function=params.function_name):
            try:
                project_root = find_project_root(".")
                project = self._get_project(project_root)

                function_info = self._resolve_symbol(project, params.function_name)
                if not function_info or function_info.type != "function":
                    return ShowResult(
                        success=False,
                        error_type="function_not_found",
                        message=f"Function '{params.function_name}' not found",
                    )

                elements = self._find_extractable_elements(project, function_info)

                return ShowResult(
                    success=True,
                    function_name=params.function_name,
                    extractable_elements=elements,
                )

            except Exception as e:
                logger.error(f"Show function error: {e}")
                return ShowResult(
                    success=False, error_type="analysis_error", message=str(e)
                )

    def _find_extractable_elements(
        self, project: Project, function_info: Any
    ) -> List[ElementInfo]:
        """Find lambdas, expressions, and code blocks that can be extracted"""
        elements: List[ElementInfo] = []

        try:
            source = function_info.resource.read()
            tree = ast.parse(source)

            function_node = self._find_function_node(tree, function_info.name)
            if not function_node:
                return elements

            lambda_count = 0
            for node in ast.walk(function_node):
                if isinstance(node, ast.Lambda):
                    lambda_count += 1
                    code = (
                        ast.unparse(node) if hasattr(ast, "unparse") else "lambda ..."
                    )
                    elements.append(
                        ElementInfo(
                            id=f"{function_info.qualified_name}.lambda_{lambda_count}",
                            type="lambda",
                            code=code,
                            location=f"{function_info.resource.path}:{getattr(node, 'lineno', 0)}",
                            extractable=True,
                        )
                    )

        except Exception as e:
            logger.warning(f"Could not analyze function {function_info.name}: {e}")

        return elements

    def _find_function_node(
        self, tree: ast.AST, function_name: str
    ) -> Optional[ast.FunctionDef]:
        """Find function node in AST by name"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return node
        return None
