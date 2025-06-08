# Refactor MCP - Implementation Plan

## Overview

Build a pluggable AST refactoring system starting with CLI for rapid iteration, then add MCP interface for Claude Code integration. Focus on Python/Rope first, designed for easy expansion.

**Project Management**: Use GitHub Issues and Projects for tracking progress, with Claude Code managing issue creation and updates throughout development.

## Phase 1: Core Foundation & CLI

### 1.1 Project Structure Setup

See **[Project Structure](project-structure.md)** for the complete package layout and module organization.

### 1.2 Core Data Models (Pydantic)

Define all the shared data structures:

- `Position`, `Range`, `SymbolInfo`
- `RenameParams`, `ExtractParams`, `AnalyzeParams`
- `RenameResult`, `ExtractResult`, `AnalysisResult`
- `ErrorResponse`, `BackupResult`

### 1.3 Provider Interface Protocol

Define the `RefactoringProvider` protocol that all providers must implement:

- `supports_language()`
- `analyze_symbol()`, `rename_symbol()`, `extract_method()`
- `find_references()`, `backup_files()`

### 1.4 Basic CLI Framework

Set up Click-based CLI with core commands:

- `refactor-mcp analyze <symbol>`
- `refactor-mcp rename <symbol> <new-name>`
- `refactor-mcp find <pattern>`

**Milestone**: CLI framework responds to commands with mock data

**GitHub Setup**:

- Create repository with initial project structure
- Set up GitHub Issues for each implementation task
- Create GitHub Project board with phase-based columns
- Document architecture decisions in GitHub Discussions

## Phase 2: Rope Provider Implementation

### 2.1 Rope Integration Layer

Build the core Rope wrapper:

- Project initialization and management
- Position ↔ byte offset conversion utilities
- Rope error handling and translation
- Symbol resolution and qualification

### 2.2 Symbol Analysis

Implement `analyze_symbol()`:

- Get symbol at position using Rope's `get_pyname_at()`
- Extract symbol info (name, type, scope, definition location)
- Find all references across project
- Return structured `AnalysisResult`

### 2.3 Symbol Renaming

Implement `rename_symbol()`:

- Use Rope's `Rename` refactoring class
- Handle qualified name resolution
- Detect and report conflicts
- Create backups before changes
- Return detailed `RenameResult`

### 2.4 Reference Finding

Implement `find_references()`:

- Search for symbols by name/pattern
- Support wildcard patterns (`auth.*`, `*.help`)
- Return qualified names and locations
- Handle disambiguation

**Milestone**: CLI can analyze and rename Python symbols end-to-end

**GitHub Tracking**:

- Create issues for each Rope integration component
- Track progress on GitHub Project board
- Use issue templates for bug reports and feature requests
- Document API decisions and edge cases in issue discussions

## Phase 3: Advanced Rope Features

### 3.1 Method Extraction

Implement `extract_method()` for named functions:

- Use Rope's `ExtractMethod` refactoring
- Handle parameter detection
- Support extracting entire functions initially
- Return `ExtractResult` with new method signature

### 3.2 Anonymous Element Discovery

Implement the `show` command:

- Parse function AST to find lambdas, expressions, complex blocks
- Generate stable IDs (`function.lambda_1`, `function.expression_2`)
- Return structured list of extractable elements

### 3.3 ID-Based Extraction

Extend extraction to support discovered element IDs:

- `extract "users.process_user.lambda_1" "is_adult"`
- Convert IDs back to precise byte ranges for Rope
- Handle lambda and expression extraction

### 3.4 Backup/Restore System

Implement safety mechanisms:

- Create timestamped backups before refactoring
- Store backup metadata (files, operations)
- Restore from backups when needed
- Cleanup old backups

**Milestone**: CLI handles all core refactoring operations including anonymous elements

**GitHub Integration**:

- Create detailed issues for complex features (lambda extraction, ID generation)
- Use GitHub releases to track major milestones
- Document testing procedures and edge cases in wiki
- Link commits to issues for traceability

## Phase 4: CLI Polish & Testing

### 4.1 Error Handling

Robust error handling for:

- Ambiguous symbol names → helpful disambiguation
- Symbol not found → suggestions
- Rope errors → user-friendly messages
- File system errors → clear guidance

### 4.2 Output Formatting

Clean CLI output:

- Human-readable success messages
- `--json` flag for structured output
- Progress indicators for long operations
- Colored output for better UX

### 4.3 Language Detection & Project Discovery

Smart defaults:

- Detect language from file extensions
- Find project root (look for `.git`, `pyproject.toml`, etc.)
- Handle relative vs absolute paths
- Validate project structure

### 4.4 Comprehensive Testing

Test suite covering:

- Unit tests for each provider method
- Integration tests with real Python projects
- Edge cases (missing files, invalid syntax)
- Error conditions and recovery

**Milestone**: Production-ready CLI tool

**GitHub Organization**:

- Tag stable CLI release on GitHub
- Create comprehensive README with usage examples
- Set up GitHub Actions for automated testing
- Use GitHub Projects to plan MCP integration phase

## Phase 5: MCP Server Layer

### 5.1 FastMCP Integration

Add MCP server alongside CLI:

- Same core logic, different interface
- Pydantic model validation for tool parameters
- Structured JSON responses
- Error handling that works for LLMs

### 5.2 MCP Tool Definitions

Convert CLI commands to MCP tools:

- `refactor_analyze_symbol(file_path, line, column)`
- `refactor_rename_symbol(file_path, line, column, new_name)`
- `refactor_find_symbols(pattern)`
- `refactor_show_function(function_name)`
- `refactor_extract_element(source, new_name)`

### 5.3 Claude Code Optimization

LLM-friendly features:

- Clear parameter validation with helpful error messages
- Consistent response formats
- Appropriate timeout handling
- Discovery workflows that guide LLM usage

**Milestone**: MCP server working with Claude Code

**GitHub Collaboration**:

- Create issues for Claude Code integration testing
- Document MCP tool usage patterns in repository wiki
- Use GitHub Discussions for LLM interface design decisions
- Track Claude Code feedback and improvements in issues

## Phase 6: Future Expansion Framework

### 6.1 Provider Registry

Clean extension points:

- Dynamic provider registration
- Language capability detection
- Provider selection logic
- Performance monitoring

### 6.2 Tree-sitter Provider (Phase 2 expansion)

Basic multi-language support:

- JavaScript, Rust, Elixir, Go
- Simple rename and basic extract operations
- Fallback when no specialized provider exists

### 6.3 Documentation & Examples

Comprehensive docs:

- API documentation
- CLI usage examples
- Provider development guide
- Claude Code integration examples

## Key Implementation Decisions

### Start with CLI First

- Faster iteration and debugging
- Easier testing with real projects
- Human validation of refactoring results
- CLI experience informs MCP design

### Rope Provider Excellence

- Deep Python support before breadth
- Handle all Rope capabilities properly
- Robust error handling for edge cases
- Performance optimization for large projects

### Clean Architecture

- Provider pattern enables easy expansion
- Shared core logic between CLI and MCP
- Consistent data models throughout
- Pluggable components for testing

### LLM-Optimized Design

- Explicit interfaces (no hidden state)
- Structured error responses
- Discovery workflows for complex cases
- Predictable behavior patterns

## Success Criteria

**Phase 1-2**: Working CLI that can rename Python functions across a real project
**Phase 3-4**: CLI handles all core operations including lambdas and expressions  
**Phase 5**: Claude Code can successfully execute multi-step refactoring workflows
**Phase 6**: Architecture proven extensible with second provider

## GitHub Integration Strategy

### Repository Organization

- **Main Branch**: Stable, working code only
- **Development Branch**: Active development and integration
- **Feature Branches**: Individual components and experiments
- **Releases**: Tagged milestones with changelog and binaries

### Issue Management

- **Epic Issues**: One per phase (Phase 1: Core Foundation, etc.)
- **Feature Issues**: Specific functionality (Rope Provider, CLI Commands)
- **Bug Issues**: Problems discovered during development/testing
- **Enhancement Issues**: Future improvements and optimizations

### Project Board Workflow

- **Backlog**: Planned features and improvements
- **In Progress**: Currently being developed
- **Review**: Ready for testing and feedback
- **Done**: Completed and merged

### Claude Code Integration

- **Automated Issue Creation**: Claude Code can create GitHub issues for bugs and features
- **Progress Tracking**: Update issue status as development progresses
- **Documentation**: Maintain architecture docs and decisions in repository
- **Release Management**: Claude Code can assist with release notes and versioning

This approach leverages GitHub's project management capabilities while enabling Claude Code to actively participate in planning and tracking development progress.
