# Architecture Overview

refactor-mcp implements a pluggable refactoring architecture with dual interfaces (MCP + CLI) built around the Provider pattern. This document provides a high-level overview - see the detailed documents below for specific areas.

## Core Architecture Components

### Provider Pattern

**Standard interface for all refactoring engines:**

```python
from typing import Protocol, List, Optional
from pydantic import BaseModel

class RefactoringProvider(Protocol):
    """Standard interface for all refactoring engines"""

    def supports_language(self, language: str) -> bool:
        """Check if this provider handles the given language"""

    def get_capabilities(self, language: str) -> List[str]:
        """Return list of supported operations for language"""

    def rename_symbol(self, params: RenameParams) -> RenameResult:
        """Safely rename symbol across scope"""

    def find_symbols(self, params: FindParams) -> FindResult:
        """Find symbols matching a pattern"""

    def analyze_symbol(self, params: AnalyzeParams) -> AnalysisResult:
        """Get symbol information and refactoring opportunities"""

    def show_function(self, params: ShowParams) -> ShowResult:
        """Show extractable elements within a function"""

    def extract_element(self, params: ExtractParams) -> ExtractResult:
        """Extract code element (function, lambda, expression, or block)"""
```

**Provider Registry and Language Detection:**

```python
class RefactoringEngine:
    """Central registry and router for refactoring providers"""

    def __init__(self):
        self.providers: List[RefactoringProvider] = []
        self._language_cache: Dict[str, RefactoringProvider] = {}

    def register_provider(self, provider: RefactoringProvider):
        """Register a new refactoring provider"""
        self.providers.append(provider)
        self._language_cache.clear()

    def get_provider(self, language: str) -> Optional[RefactoringProvider]:
        """Get best provider for language (cached)"""
        if language not in self._language_cache:
            for provider in self.providers:
                if provider.supports_language(language):
                    self._language_cache[language] = provider
                    break
            else:
                self._language_cache[language] = None

        return self._language_cache[language]

# Global engine instance
engine = RefactoringEngine()
```

**Language and Project Detection:**

```python
def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    suffix = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.rs': 'rust',
        '.ex': 'elixir',
        '.go': 'go'
    }
    return language_map.get(suffix, 'unknown')

def find_project_root(start_path: str) -> str:
    """Find project root by looking for markers"""
    current = Path(start_path).absolute()
    markers = ['.git', 'pyproject.toml', 'setup.py', 'Cargo.toml', 'package.json']

    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return str(current)
        current = current.parent

    return str(Path(start_path).absolute())
```

### Data Models
- **Pydantic-based** parameter and response models
- **Consistent validation** across all operations
- **Structured error responses** with actionable suggestions

See **[Data Models](data-models.md)** for complete model definitions.

### Dual Interface System

#### MCP Server Interface
- **AI-optimized tools** for programmatic consumption
- **FastMCP framework** with automatic validation
- **Structured JSON responses** for LLM consumption

See **[MCP Interface](mcp-interface.md)** for tool specifications.

#### CLI Interface  
- **Human-friendly commands** for testing and debugging
- **Click-based** with JSON output option
- **Rich formatting** for development workflows

See **[CLI Interface](cli-interface.md)** for command reference.

## Architecture Principles

The system follows core design principles:

1. **Explicit Over Implicit** - No hidden state, predictable behavior
2. **Safety First** - Conflict detection, backups, validation
3. **LLM-Optimized** - Symbol-first operations, discovery-driven workflows
4. **Extensible Foundation** - Pluggable providers for multiple languages

See **[Design Principles](design-principles.md)** for detailed guidelines.

## Provider Implementations

### Phase 1: Rope Provider (Python)
- **Battle-tested** Python refactoring engine
- **Full symbol analysis** and safe renaming
- **Method extraction** with parameter detection

### Phase 2: Tree-sitter Provider (Multi-language)
- **Universal parsing** for JavaScript, Rust, Elixir, Go
- **Consistent interface** across languages
- **Basic refactoring operations**

### Phase 3: Specialized Providers
- **rust-analyzer** for advanced Rust refactoring
- **LibCST** for Python formatting-aware operations
- **Language-specific optimizations**

## Key Operations (MVP)

1. **Symbol Analysis** (`analyze`) - Get symbol information and refactoring opportunities
2. **Symbol Discovery** (`find`) - Search for symbols matching patterns
3. **Function Exploration** (`show`) - Discover extractable elements within functions
4. **Symbol Renaming** (`rename`) - Safe cross-scope renaming with conflict detection
5. **Element Extraction** (`extract`) - Extract functions, lambdas, expressions, or blocks

## Interface Design Philosophy

### Symbol-First Operations
Use qualified names (`auth.utils.login`) rather than file positions for reliability.

### Discovery-Driven Workflow
```bash
# 1. Find what's available
refactor_find_symbols "validation"

# 2. Analyze specific symbols  
refactor_analyze_symbol "auth.validate_user"

# 3. Perform operations
refactor_rename_symbol "auth.validate_user" "authenticate_user"
```

### Error-Driven Learning
Ambiguous operations fail with helpful suggestions:
```json
{
  "error_type": "ambiguous_symbol",
  "message": "Multiple 'help' symbols found", 
  "suggestions": ["Use qualified names: 'auth.utils.help' or 'database.utils.help'"]
}
```

## Project Structure

```
refactor_mcp/
├── shared/           # Core utilities (logging, observability)
├── providers/        # Refactoring engine implementations
│   ├── rope_provider.py
│   └── treesitter_provider.py  
├── cli/             # Command-line interface
├── server/          # MCP server implementation
└── models/          # Pydantic data models
```

## Related Documentation

- **[Project Plan](project-plan.md)** - Goals, scope, and success metrics  
- **[CLI Interface](cli-interface.md)** - Command-line interface specifications
- **[MCP Interface](mcp-interface.md)** - MCP server tool specifications
- **[Implementation Plan](implementation-plan.md)** - Development phases and timeline

This modular architecture ensures refactor-mcp can grow from Python-focused tool to universal refactoring platform while maintaining consistent, AI-friendly interfaces.