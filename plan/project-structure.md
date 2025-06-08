# Project Structure

Code organization and module layout for refactor-mcp.

## Package Layout

```
refactor_mcp/
├── __init__.py                 # Package initialization and version
├── __main__.py                 # CLI entry point
├── shared/                     # Core utilities
│   ├── __init__.py
│   ├── logging.py              # Logging configuration
│   └── observability.py        # Metrics and operation tracking
├── models/                     # Pydantic data models
│   ├── __init__.py
│   ├── params.py               # Parameter models (AnalyzeParams, RenameParams, etc.)
│   ├── responses.py            # Response models (AnalysisResult, RenameResult, etc.)
│   └── errors.py               # Error response models
├── providers/                  # Refactoring engine implementations
│   ├── __init__.py
│   ├── base.py                 # RefactoringProvider protocol definition
│   ├── rope_provider.py        # Python Rope implementation
│   ├── treesitter_provider.py  # Tree-sitter multi-language provider
│   └── registry.py             # Provider registry and engine
├── cli/                        # Command-line interface
│   ├── __init__.py
│   ├── main.py                 # Click-based CLI commands
│   ├── formatters.py           # Output formatting utilities
│   └── utils.py                # CLI helper functions
├── server/                     # MCP server implementation
│   ├── __init__.py
│   ├── mcp_server.py           # FastMCP server setup and tools
│   ├── handlers.py             # Tool implementation handlers
│   └── middleware.py           # Debugging and logging middleware
└── utils/                      # Shared utilities
    ├── __init__.py
    ├── language_detection.py   # Language and project detection
    ├── backup.py               # Backup creation and restoration
    └── validation.py           # Input validation helpers
```

## Module Responsibilities

### Core Package (`refactor_mcp/`)

**`__init__.py`**
- Package version and metadata
- Public API exports
- Provider registration

**`__main__.py`**
- CLI entry point when running `python -m refactor_mcp`
- Imports and invokes CLI main function

### Shared Utilities (`shared/`)

**`logging.py`**
- Centralized logging configuration
- Debug, info, error logging levels
- File and console output options

**`observability.py`**
- Operation metrics and timing
- Context managers for tracking operations
- Performance monitoring utilities

### Data Models (`models/`)

**`params.py`**
```python
# Input parameter models
class AnalyzeParams(BaseModel): ...
class RenameParams(BaseModel): ...
class ExtractParams(BaseModel): ...
class FindParams(BaseModel): ...
class ShowParams(BaseModel): ...
```

**`responses.py`**
```python
# Success response models
class AnalysisResult(BaseModel): ...
class RenameResult(BaseModel): ...
class ExtractResult(BaseModel): ...
class FindResult(BaseModel): ...
class ShowResult(BaseModel): ...
```

**`errors.py`**
```python
# Error response models and utilities
class ErrorResponse(BaseModel): ...
def create_error_response(...): ...
```

### Provider System (`providers/`)

**`base.py`**
```python
# Protocol definition
class RefactoringProvider(Protocol): ...

# Common interfaces and utilities
class BaseProvider: ...
```

**`rope_provider.py`**
```python
# Python Rope implementation
class RopeProvider(RefactoringProvider): ...
```

**`registry.py`**
```python
# Provider registry and routing
class RefactoringEngine: ...
engine = RefactoringEngine()  # Global instance
```

### CLI Interface (`cli/`)

**`main.py`**
```python
# Click command definitions
@click.group()
def refactor(): ...

@refactor.command()
def analyze(): ...
# ... other commands
```

**`formatters.py`**
```python
# Human-readable output formatting
def format_analysis_output(result: AnalysisResult): ...
def format_find_output(result: FindResult): ...
# ... other formatters
```

### MCP Server (`server/`)

**`mcp_server.py`**
```python
# FastMCP server setup
mcp = fastmcp.FastMCP("refactor-mcp")

@mcp.tool()
def refactor_analyze_symbol(): ...
# ... other tools
```

**`handlers.py`**
```python
# Tool implementation logic
def handle_analyze_symbol(params: AnalyzeParams): ...
def handle_rename_symbol(params: RenameParams): ...
# ... other handlers
```

### Utilities (`utils/`)

**`language_detection.py`**
```python
def detect_language_from_file(file_path: str) -> str: ...
def detect_project_language() -> str: ...
def find_project_root(start_path: str) -> str: ...
```

**`backup.py`**
```python
def create_backup(files: List[str]) -> str: ...
def restore_backup(backup_id: str) -> bool: ...
def list_backups() -> List[str]: ...
```

## Import Structure

### Public API (`refactor_mcp/__init__.py`)

```python
"""refactor-mcp: AST refactoring engine for LLM consumption"""

__version__ = "0.1.0"

# Public API exports
from .providers.registry import engine
from .models.params import AnalyzeParams, RenameParams, ExtractParams
from .models.responses import AnalysisResult, RenameResult, ExtractResult
from .models.errors import ErrorResponse

# Register default providers
from .providers.rope_provider import RopeProvider
engine.register_provider(RopeProvider())

__all__ = [
    "engine",
    "AnalyzeParams", "RenameParams", "ExtractParams",
    "AnalysisResult", "RenameResult", "ExtractResult", 
    "ErrorResponse"
]
```

### CLI Entry Point (`refactor_mcp/__main__.py`)

```python
"""CLI entry point for refactor-mcp"""

from .cli.main import refactor

if __name__ == "__main__":
    refactor()
```

## Configuration and Settings

### Environment Variables

- `REFACTOR_MCP_DEBUG`: Enable debug logging and middleware
- `REFACTOR_MCP_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `REFACTOR_MCP_LOG_FILE`: Optional log file path
- `REFACTOR_MCP_BACKUP_DIR`: Custom backup directory (default: `.refactor-backups`)

### Project Detection

The system automatically detects project root by searching for:
- `.git` directory
- `pyproject.toml`, `setup.py` (Python)
- `package.json` (JavaScript/TypeScript)
- `Cargo.toml` (Rust)
- `mix.exs` (Elixir)
- `go.mod` (Go)

### Language Detection

File extension mapping:
- `.py` → `python` (Rope provider)
- `.js`, `.ts` → `javascript`/`typescript` (Tree-sitter provider)
- `.rs` → `rust` (Tree-sitter or rust-analyzer provider)
- `.ex`, `.exs` → `elixir` (Tree-sitter provider)
- `.go` → `go` (Tree-sitter provider)

## Testing Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── unit/                       # Unit tests
│   ├── test_models.py          # Model validation tests
│   ├── test_providers/         # Provider implementation tests
│   ├── test_cli/               # CLI command tests
│   └── test_server/            # MCP server tests
├── integration/                # Integration tests
│   ├── test_workflows.py       # End-to-end refactoring workflows
│   └── test_providers/         # Provider integration tests
└── fixtures/                   # Test data and mock projects
    ├── python_project/         # Sample Python project for testing
    └── multi_language/         # Multi-language test project
```

This structure provides clear separation of concerns while maintaining consistent interfaces across all components.