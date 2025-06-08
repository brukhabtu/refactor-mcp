# Rope Provider Implementation

Python-specific refactoring implementation using the Rope library for Phase 1 MVP.

## Rope Provider Overview

The RopeProvider implements the RefactoringProvider protocol using Python's Rope library, providing battle-tested AST-based refactoring for Python codebases.

## Core Implementation

```python
from rope.base.project import Project
from rope.base.resources import File
from rope.refactor.rename import Rename
from rope.refactor.extract import ExtractMethod
from rope.contrib.findit import find_occurrences

class RopeProvider(RefactoringProvider):
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
                "show_function"
            ]
        return []
```

## Project Management

### Project Caching

```python
def _get_project(self, project_root: str) -> Project:
    """Get or create cached Rope project"""
    if project_root not in self._project_cache:
        # Configure Rope project settings
        prefs = {
            'python_files': ['*.py'],
            'save_objectdb': True,
            'compress_objectdb': False,
            'automatic_soa': True,
            'soa_followed_calls': 0,
            'perform_doa': True,
            'validate_objectdb': True,
            'max_history_items': 32,
            'save_history': True,
            'ignore_syntax_errors': False,
            'ignore_bad_imports': False
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
```

### Resource Resolution

```python
def _find_resource(self, project: Project, symbol_name: str) -> Optional[File]:
    """Find the file containing a symbol"""
    # Try direct module lookup first
    if '.' in symbol_name:
        module_path = symbol_name.replace('.', os.sep) + '.py'
        resource = project.get_resource(module_path)
        if resource.exists():
            return resource
    
    # Fall back to project-wide search
    for resource in project.get_files():
        if resource.name.endswith('.py'):
            try:
                source = resource.read()
                if symbol_name in source:
                    return resource
            except:
                continue
    
    return None
```

## Symbol Operations

### Symbol Analysis

```python
def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
    """Analyze Python symbol using Rope"""
    try:
        project_root = find_project_root(".")
        project = self._get_project(project_root)
        
        # Find symbol location
        symbol_info = self._resolve_symbol(project, params.symbol_name)
        if not symbol_info:
            return AnalysisResult(
                success=False,
                error_type="symbol_not_found",
                message=f"Symbol '{params.symbol_name}' not found"
            )
        
        # Get references using Rope's find_occurrences
        references = find_occurrences(
            project, 
            symbol_info.resource, 
            symbol_info.offset
        )
        
        # Analyze refactoring opportunities
        suggestions = self._analyze_refactoring_opportunities(
            project, symbol_info
        )
        
        return AnalysisResult(
            success=True,
            symbol_info=SymbolInfo(
                name=symbol_info.name,
                qualified_name=params.symbol_name,
                type=symbol_info.type,
                definition_location=f"{symbol_info.resource.path}:{symbol_info.line}",
                scope=symbol_info.scope,
                docstring=symbol_info.docstring
            ),
            references=[ref.resource.path for ref in references],
            reference_count=len(references),
            refactoring_suggestions=suggestions
        )
        
    except Exception as e:
        return AnalysisResult(
            success=False,
            error_type="analysis_error", 
            message=str(e)
        )
```

### Symbol Discovery

```python
def find_symbols(self, params: FindParams) -> FindResult:
    """Find symbols matching pattern using Rope"""
    try:
        project_root = find_project_root(".")
        project = self._get_project(project_root)
        
        matches = []
        pattern = params.pattern.lower()
        
        # Search through all Python files
        for resource in project.get_files():
            if not resource.name.endswith('.py'):
                continue
                
            try:
                # Parse file and extract symbols
                module_symbols = self._extract_module_symbols(project, resource)
                
                # Filter by pattern
                for symbol in module_symbols:
                    if self._matches_pattern(symbol.name, pattern):
                        matches.append(symbol)
                        
            except Exception:
                # Skip files with parse errors
                continue
        
        return FindResult(
            success=True,
            pattern=params.pattern,
            matches=matches[:100],  # Limit results
            total_count=len(matches)
        )
        
    except Exception as e:
        return FindResult(
            success=False,
            error_type="search_error",
            message=str(e)
        )

def _matches_pattern(self, symbol_name: str, pattern: str) -> bool:
    """Check if symbol matches search pattern"""
    import fnmatch
    
    # Support wildcards
    if '*' in pattern or '?' in pattern:
        return fnmatch.fnmatch(symbol_name.lower(), pattern)
    
    # Simple substring match
    return pattern in symbol_name.lower()
```

### Symbol Renaming

```python
def rename_symbol(self, params: RenameParams) -> RenameResult:
    """Safely rename Python symbol using Rope"""
    try:
        project_root = find_project_root(".")
        project = self._get_project(project_root)
        
        # Find symbol to rename
        symbol_info = self._resolve_symbol(project, params.symbol_name)
        if not symbol_info:
            return RenameResult(
                success=False,
                error_type="symbol_not_found",
                message=f"Symbol '{params.symbol_name}' not found"
            )
        
        # Check for naming conflicts
        conflicts = self._check_rename_conflicts(
            project, symbol_info, params.new_name
        )
        if conflicts:
            return RenameResult(
                success=False,
                error_type="naming_conflict",
                message="Renaming would create conflicts",
                conflicts=conflicts
            )
        
        # Create backup
        backup_id = self._create_backup(project)
        
        # Perform rename using Rope
        renamer = Rename(project, symbol_info.resource, symbol_info.offset)
        changes = renamer.get_changes(params.new_name)
        
        # Apply changes
        project.do(changes)
        
        # Collect results
        files_modified = [change.resource.path for change in changes.changes]
        references_updated = len(changes.changes)
        
        return RenameResult(
            success=True,
            old_name=params.symbol_name,
            new_name=params.new_name,
            qualified_name=symbol_info.qualified_name,
            files_modified=files_modified,
            references_updated=references_updated,
            backup_id=backup_id
        )
        
    except Exception as e:
        return RenameResult(
            success=False,
            error_type="rename_error",
            message=str(e)
        )
```

### Method Extraction

```python
def extract_element(self, params: ExtractParams) -> ExtractResult:
    """Extract Python code element using Rope"""
    try:
        project_root = find_project_root(".")
        project = self._get_project(project_root)
        
        # Parse source specification
        source_info = self._parse_extraction_source(params.source)
        if not source_info:
            return ExtractResult(
                success=False,
                error_type="invalid_source",
                message=f"Cannot parse source: {params.source}"
            )
        
        # Find target resource and location
        resource = self._find_resource(project, source_info.module)
        if not resource:
            return ExtractResult(
                success=False,
                error_type="resource_not_found",
                message=f"Cannot find module: {source_info.module}"
            )
        
        # Determine extraction range
        start_offset, end_offset = self._get_extraction_range(
            project, resource, source_info
        )
        
        # Create backup
        backup_id = self._create_backup(project)
        
        # Perform extraction using Rope
        extractor = ExtractMethod(project, resource, start_offset, end_offset)
        changes = extractor.get_changes(params.new_name)
        
        # Apply changes
        project.do(changes)
        
        # Analyze extracted function
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
            backup_id=backup_id
        )
        
    except Exception as e:
        return ExtractResult(
            success=False,
            error_type="extraction_error",
            message=str(e)
        )
```

## Function Analysis

### Extractable Element Discovery

```python
def show_function(self, params: ShowParams) -> ShowResult:
    """Show extractable elements within Python function"""
    try:
        project_root = find_project_root(".")
        project = self._get_project(project_root)
        
        # Find function
        function_info = self._resolve_symbol(project, params.function_name)
        if not function_info or function_info.type != "function":
            return ShowResult(
                success=False,
                error_type="function_not_found",
                message=f"Function '{params.function_name}' not found"
            )
        
        # Parse function AST to find extractable elements
        elements = self._find_extractable_elements(project, function_info)
        
        return ShowResult(
            success=True,
            function_name=params.function_name,
            extractable_elements=elements
        )
        
    except Exception as e:
        return ShowResult(
            success=False,
            error_type="analysis_error",
            message=str(e)
        )

def _find_extractable_elements(self, project: Project, function_info) -> List[ElementInfo]:
    """Find lambdas, expressions, and code blocks that can be extracted"""
    import ast
    
    elements = []
    
    # Parse function source
    source = function_info.resource.read()
    tree = ast.parse(source)
    
    # Find function node
    function_node = self._find_function_node(tree, function_info.name)
    if not function_node:
        return elements
    
    # Extract lambda expressions
    for i, node in enumerate(ast.walk(function_node)):
        if isinstance(node, ast.Lambda):
            elements.append(ElementInfo(
                id=f"{function_info.qualified_name}.lambda_{i+1}",
                type="lambda",
                code=ast.unparse(node),
                location=f"{function_info.resource.path}:{node.lineno}",
                extractable=True
            ))
    
    # Extract complex expressions
    # Extract code blocks
    # ... additional extraction logic
    
    return elements
```

## Error Handling

### Rope-Specific Error Mapping

```python
def _handle_rope_error(self, error: Exception) -> ErrorResponse:
    """Map Rope exceptions to standardized error responses"""
    
    error_mappings = {
        "BadIdentifierError": ("invalid_name", ["Name must be a valid Python identifier"]),
        "RefactoringError": ("refactoring_failed", ["Check syntax and symbol existence"]),
        "ModuleNotFoundError": ("module_not_found", ["Ensure module is in Python path"]),
        "ResourceNotFoundError": ("file_not_found", ["Check file path and permissions"])
    }
    
    error_type = type(error).__name__
    error_info = error_mappings.get(error_type, ("internal_error", []))
    
    return ErrorResponse(
        error_type=error_info[0],
        message=str(error),
        suggestions=error_info[1]
    )
```

## Performance Optimizations

### Caching Strategy

```python
def _cache_symbol_info(self, project: Project, symbol_name: str, info: Any):
    """Cache symbol information for faster lookups"""
    cache_key = (project.address, symbol_name)
    self._symbol_cache[cache_key] = info

def _get_cached_symbol_info(self, project: Project, symbol_name: str) -> Any:
    """Retrieve cached symbol information"""
    cache_key = (project.address, symbol_name)
    return self._symbol_cache.get(cache_key)
```

This Rope provider implementation provides robust Python refactoring capabilities while maintaining the consistent interface expected by the refactor-mcp system.