# Design Principles

Core design philosophy and guidelines for refactor-mcp development.

## 1. Explicit Over Implicit

**Principle**: No hidden state or implicit context. Every operation is self-contained and predictable.

### Interface Design Philosophy

After extensive analysis of LLM interaction patterns, we've chosen an **explicit-first** interface design that prioritizes predictability over convenience.

#### Core Interface Principles

1. **No Hidden State** - Each command is self-contained, no persistent context between operations
2. **Explicit Disambiguation** - Ambiguous operations fail with helpful suggestions rather than guessing  
3. **Position-Based Precision** - Support exact positioning for complex extractions when needed
4. **Working Directory Convention** - Follow standard UNIX tools (git, make, etc.) for project detection

### Implementation Guidelines

- **No persistent context between operations**: Each command starts with a clean slate
- **Working directory follows UNIX convention**: Tool searches upward from current directory for project root
- **Explicit disambiguation**: Ambiguous operations fail with helpful suggestions rather than guessing

### Examples

```python
# Good: Explicit, self-contained
refactor-mcp rename "auth.utils.login" "authenticate"

# Bad: Relies on hidden context
refactor-mcp set-context "auth.utils"
refactor-mcp rename "login" "authenticate"  # Unclear which login
```

## 2. Safety First

**Principle**: Prioritize code safety and reliability over convenience. Never break working code.

### Implementation Guidelines

- **Conflict detection**: Always check for naming conflicts before operations
- **Automatic backups**: Create backups before destructive operations
- **Validation at boundaries**: Validate all inputs with clear error messages
- **Rollback mechanisms**: Provide ways to undo operations if needed

### Safety Checklist

- [ ] Input validation with Pydantic models
- [ ] Symbol existence verification before operations
- [ ] Conflict detection for renames and extractions
- [ ] Backup creation before file modifications
- [ ] Test coverage for edge cases and error conditions

## 3. LLM-Optimized

**Principle**: Design interfaces specifically for AI system consumption, not just human convenience.

### Interface Design for LLMs

- **Symbol-first operations**: Use qualified names (`auth.utils.login`) rather than file positions
- **Discovery-driven workflow**: Provide tools to find what exists before operating on it
- **Error-driven learning**: Clear disambiguation with actionable suggestions
- **Structured responses**: JSON output with consistent error formats

### LLM Interaction Patterns

```python
# Pattern 1: Discovery → Analysis → Action
refactor_find_symbols("validation")           # Find all validation-related symbols
refactor_analyze_symbol("auth.validate_user") # Analyze specific symbol
refactor_rename_symbol("auth.validate_user", "authenticate_user")

# Pattern 2: Function exploration → Element extraction
refactor_show_function("users.process_user")  # Show extractable elements
refactor_extract_element("users.process_user.lambda_1", "is_adult")
```

## 4. Extensible Foundation

**Principle**: Build for multiple languages and providers while maintaining consistent interfaces.

### Provider Architecture

- **Protocol-based design**: Standard interface all providers must implement
- **Language detection**: Automatic routing to appropriate providers
- **Capability reporting**: Providers declare what operations they support
- **Graceful degradation**: Clear error messages when operations aren't supported

### Extension Points

```python
# New language support
class TypeScriptProvider(RefactoringProvider):
    def supports_language(self, language: str) -> bool:
        return language == "typescript"
    
    def get_capabilities(self, language: str) -> List[str]:
        return ["rename_symbol", "find_symbols", "analyze_symbol"]

# Register new provider
engine.register_provider(TypeScriptProvider())
```

## 5. Progressive Complexity

**Principle**: Simple cases should be simple, complex cases should be possible.

### Interface Layers

1. **Simple symbol names** - For unambiguous cases: `rename "login" "authenticate"`
2. **Qualified names** - For disambiguation: `rename "auth.utils.login" "authenticate"`
3. **Element IDs** - For anonymous elements: `extract "function.lambda_1" "is_valid"`
4. **Position-based** - For complex edge cases: Future enhancement

### Discovery Mechanisms

- **On-demand complexity**: Only show detailed information when ambiguity exists
- **Graduated disclosure**: Start simple, provide more detail as needed
- **Auto-generated IDs**: Stable references for elements that lack names

## 6. Error Handling Philosophy

**Principle**: Fail fast with helpful guidance. Errors should teach, not frustrate.

### Error Response Standards

```python
class ErrorResponse(BaseModel):
    success: bool = False
    error_type: str          # Machine-readable error category
    message: str             # Human-readable description
    suggestions: List[str]   # Actionable next steps
```

### Error Categories

- **validation_error**: Input doesn't meet requirements
- **symbol_not_found**: Requested symbol doesn't exist
- **ambiguous_symbol**: Multiple matches found
- **provider_not_found**: No support for detected language
- **operation_failed**: Provider operation encountered error

### Suggestion Patterns

```python
# Ambiguity resolution
{
  "error_type": "ambiguous_symbol",
  "message": "Multiple 'help' symbols found",
  "suggestions": [
    "Use qualified names: 'auth.utils.help' or 'database.utils.help'",
    "Run 'refactor_find_symbols help' to see all matches"
  ]
}

# Discovery guidance
{
  "error_type": "symbol_not_found", 
  "message": "Symbol 'nonexistent_function' not found",
  "suggestions": [
    "Did you mean: existing_function, another_function?",
    "Use 'refactor_find_symbols' to discover available symbols"
  ]
}
```

## 7. Performance Considerations

**Principle**: Operations should be fast enough for interactive use while handling large codebases.

### Performance Targets

- **Symbol lookup**: < 100ms for typical projects
- **Rename operations**: < 2s for projects with < 10k references
- **Discovery operations**: < 500ms for project-wide searches
- **Memory usage**: < 100MB for typical Python projects

### Optimization Strategies

- **Lazy loading**: Only parse files when needed
- **Caching**: Cache symbol tables and analysis results
- **Incremental updates**: Update caches when files change
- **Provider-specific optimizations**: Let Rope, Tree-sitter optimize internally

## 8. Testing Strategy

**Principle**: Test the interface contracts, not implementation details.

### Test Categories

1. **Interface compliance**: All providers implement the protocol correctly
2. **Error handling**: Proper error responses for all failure modes
3. **Safety**: Operations don't break working code
4. **Performance**: Operations complete within target times

### Mock-Based Testing

```python
class MockProvider(RefactoringProvider):
    """Predictable provider for testing interface behavior"""
    
    def __init__(self, symbols: Dict[str, SymbolInfo]):
        self.symbols = symbols
    
    def find_symbols(self, params: FindParams) -> FindResult:
        matches = [s for s in self.symbols.values() if params.pattern in s.name]
        return FindResult(success=True, pattern=params.pattern, matches=matches)
```

This design philosophy ensures refactor-mcp provides reliable, safe, and AI-friendly refactoring operations while maintaining extensibility for future enhancements.