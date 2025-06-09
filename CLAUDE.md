# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚀 Quick Start for New Sessions

**Documentation Navigation** - Use these commands to avoid duplicate work:

```bash
# Documentation overview
cat plan/README.md             # Full documentation map
cat plan/project-plan.md       # What we're building and why
cat plan/architecture.md       # Complete system design and provider pattern

# Interface specifications
cat plan/cli-interface.md      # Command-line interface
cat plan/mcp-interface.md      # MCP server tools
cat plan/data-models.md        # Pydantic models and types

# Implementation details
cat plan/rope-provider.md      # Python implementation specifics
cat plan/project-structure.md  # Code organization

# LLM workflow guidance
cat plan/llm-usage-patterns.md # Common patterns and anti-duplication
```

## Work Deduplication Strategy

### Before Starting New Work

1. **Check existing documentation**: Always read relevant plan files first
2. **Review current implementation**: Use `find refactor_mcp/ -name "*.py"` to see what exists
3. **Verify VS Code tasks**: Use existing tasks for development workflow

### Key Documentation Areas by Task Type

#### Adding New Providers
- Read: `plan/architecture.md` (Provider pattern)
- Read: `plan/rope-provider.md` (Implementation example)
- Check: `refactor_mcp/providers/` (Existing implementations)

#### Adding MCP Tools
- Read: `plan/mcp-interface.md` (Tool specifications)
- Read: `plan/data-models.md` (Request/response models)
- Check: `refactor_mcp/server/` (Existing server code)

#### CLI Development
- Read: `plan/cli-interface.md` (Command specifications)
- Check: `refactor_mcp/cli/` (Existing CLI code)
- Use: `uv run python -m refactor_mcp.cli --help` (Current state)

#### Testing
- Read: `plan/design-principles.md` (Testing philosophy)
- Check: `tests/` (Existing test structure)
- Use: `uv run pytest tests/ -v` (Run current tests)

### Anti-Patterns to Avoid

1. **Don't recreate existing documentation** - Always check plan/ first
2. **Don't implement without reading specs** - Each plan file has detailed requirements
3. **Don't skip error handling** - See `plan/design-principles.md` for error patterns
4. **Don't use different naming** - Follow established conventions in plan docs
5. **Don't create redundant files** - Use existing structure in `plan/project-structure.md`

### Implementation Status Tracking

**Phase 1 MVP (Current)**:
- [ ] Core provider interface (`plan/architecture.md`)
- [ ] Rope provider implementation (`plan/rope-provider.md`) 
- [ ] MCP server tools (`plan/mcp-interface.md`)
- [ ] CLI commands (`plan/cli-interface.md`)
- [ ] Data models (`plan/data-models.md`)

**Existing Code Structure**:
```bash
refactor_mcp/
├── shared/           # ✅ Logging and observability (basic)
│   ├── logging.py    # ✅ Implemented
│   └── observability.py  # ✅ Implemented
└── [other modules]   # ❌ Not yet implemented
```

Use `find refactor_mcp/ -name "*.py" | head -10` to check current implementation status.

## Documentation Freshness

All plan documentation was reorganized and deduplicated on 2025-06-08:
- Consistent `kebab-case.md` naming
- Focused files under 500 lines each  
- Clear cross-references between documents
- Eliminated duplication: reduced from 13 files (5,655 lines) to 11 files (2,528 lines)
- Single source of truth for all core concepts

## When Documentation is Unclear

If plan documentation doesn't cover your specific need:
1. Check if it belongs in an existing file
2. Create focused addition to appropriate plan file  
3. Update relevant cross-references
4. Maintain the kebab-case naming convention

## Project Overview

**refactor-mcp** is an AST refactoring engine designed specifically for LLM consumption through Model Context Protocol (MCP). It provides safe, reliable Python code refactoring operations that AI systems can execute autonomously.

## Essential Commands

### Development Setup
```bash
# Initial setup
uv sync

# Run all tests
uv run pytest tests/ -v

# Quick test run
uv run pytest tests/ --tb=short

# Code quality (lint + format + typecheck)
uv run ruff check . && uv run ruff format . && uv run mypy refactor_mcp/

# TDD development cycle (Red→Green→Refactor)
uv run pytest tests/test_specific.py::test_new_behavior -v && \
echo "✅ RED: Test fails as expected" && \
# [Implement minimal code] && \
uv run pytest tests/test_specific.py::test_new_behavior -v && \
echo "✅ GREEN: Test passes" && \
uv run pytest tests/ --tb=short && uv run ruff check . && uv run ruff format . && uv run mypy refactor_mcp/ && \
echo "✅ REFACTOR: All tests pass, code is clean"

# Full development cycle (after TDD iterations)
uv run pytest tests/ --tb=short && uv run ruff check . && uv run ruff format . && uv run mypy refactor_mcp/ && uv run pytest tests/ -v
```

### CLI Usage
```bash
# Run CLI help
uv run python -m refactor_mcp.cli --help
```

## Architecture

### Core Design Pattern: Pluggable Providers

The system uses a **Provider pattern** to support multiple refactoring engines:

- **Phase 1**: Rope provider (Python expertise, battle-tested)
- **Phase 2**: Tree-sitter provider (multi-language breadth)  
- **Phase 3**: Specialized providers (rust-analyzer, LibCST, etc.)

### Dual Interface System

- **MCP Server**: AI-optimized tool interface for programmatic consumption
- **CLI Interface**: Human-friendly testing, debugging, development workflow

### Key Architectural Principles

- **Explicit-First Design**: No hidden state, predictable behavior for LLM interactions
- **Symbol-First Operations**: Use qualified names (`auth.utils.login`) rather than line positions
- **Discovery-Driven Workflow**: Find → analyze → refactor patterns
- **Auto-Generated IDs**: Stable references for anonymous elements (`function.lambda_1`)

## Core Operations (MVP)

1. **Symbol Analysis** - Get symbol information (definition, type, scope)
2. **Symbol Renaming** - Safe cross-codebase renaming with conflict detection  
3. **Method Extraction** - Extract code regions into new methods
4. **Reference Finding** - Locate all symbol usages across project
5. **Anonymous Element Discovery** - Find and extract lambdas, expressions, code blocks

## Command Interface Patterns

```bash
# Symbol discovery and analysis
refactor-mcp find <symbol-pattern>
refactor-mcp analyze <symbol>
refactor-mcp show <function>              # Discover extractable elements

# Refactoring operations  
refactor-mcp rename <symbol> <new-name>
refactor-mcp extract <source> <new-name>  # Unified extract command

# Examples with qualified names
refactor-mcp rename "auth.utils.login" "authenticate"
refactor-mcp extract "users.process_user.lambda_1" "is_adult"
```

## Code Structure

### Package Layout
- `refactor_mcp/shared/` - Core utilities (logging, observability)
- `refactor_mcp/providers/` - Refactoring engine implementations  
- `refactor_mcp/cli/` - Command-line interface
- `refactor_mcp/server/` - MCP server implementation

### Key Components

- **OperationTracker**: Tracks refactoring operations for observability with context managers
- **RefactoringProvider Protocol**: Standard interface for all refactoring engines
- **RefactoringEngine**: Central registry and router for providers

## Testing Strategy

Use pytest with provider mocking. Test files should focus on:
- Provider interface compliance
- Symbol resolution accuracy  
- Refactoring safety (no code breakage)
- Error handling and disambiguation

## Development Workflow

### VS Code Integration
The project includes pre-configured VS Code tasks:
- `setup`, `test`, `test-quick`, `lint`, `typecheck`, `quality`, `dev-cycle`

### Git Workflow Tools
- `./gw.sh` - Create git worktrees for parallel development
- `./gwr.sh` - Interactive worktree cleanup
- `./dev-start.sh` - Guided development startup

### Package Management
Always use UV for dependencies:
```bash
uv add <package>  # Never edit pyproject.toml directly
```

## Error Handling Philosophy

All operations should fail explicitly with actionable suggestions:
- **Ambiguous symbols**: Return candidates with qualified names
- **Multiple extractable elements**: Show available options with auto-generated IDs
- **Symbol not found**: Provide "did you mean" suggestions

This promotes error-driven learning for LLM interactions.

## Claude Background Tasks

This project includes a Claude task management system for running background Claude Code sessions that you can check on later. This is useful for long-running operations, parallel development, and tracking conversation history.

### Basic Usage

```bash
# Start a background Claude task
.claude/ct start <name> "<message>" [directory]

# Continue an existing task
.claude/ct continue <name> "<message>"

# List all running/completed tasks
.claude/ct list

# View task conversation
.claude/ct conversation <name>

# Remove a completed task
.claude/ct remove <name>
```

### Examples

```bash
# Start a refactoring task
.claude/ct start refactor "Implement the Rope provider for symbol analysis"

# Continue the task later
.claude/ct continue refactor "Now add error handling for ambiguous symbols"

# Check task status
.claude/ct list

# View the conversation
.claude/ct conversation refactor

# Clean up completed tasks
.claude/ct remove refactor
```

### Task Management Features

- **Non-blocking execution**: Tasks run in background, return immediately
- **Conversation history**: All requests and responses are tracked
- **Session resumption**: Continue tasks with session IDs automatically
- **Collaborative management**: Both humans and AI can review, continue, and remove tasks
- **Status tracking**: Clear status indicators (awaiting_response vs response_received)
- **Git worktree support**: Isolated development environments for parallel work
- **Error handling**: Gracefully handles failed commands and non-JSON output
- **Path isolation**: Tasks run in their correct project directories

### Collaborative Task Management

**Task Lifecycle**:
1. **Start**: Either human or AI creates task with `.claude/ct start <name> "<message>" --worktree`
2. **Monitor**: Check status with `.claude/ct list` (awaiting_response → response_received)
3. **Review**: Either human or AI reviews with `.claude/ct conversation <name>`
4. **Decide**: Continue work (`.claude/ct continue <name> "<message>"`) or remove when satisfied (`.claude/ct remove <name>`)

**AI Task Management**: During interactive sessions, Claude Code can autonomously:
- Start background tasks for parallel TDD development
- Monitor task completion status and TDD compliance
- Review conversation outputs for Red→Green→Refactor patterns
- Continue tasks that need TDD refinement or missing tests
- Remove tasks when work is satisfactory and tests pass
- Orchestrate complex multi-task workflows with test coverage
- Enforce TDD discipline across all background tasks

### TDD-First Development Workflow

**Core TDD Loop** (Red → Green → Refactor):
```bash
# 1. Write failing test first
uv run pytest tests/test_new_feature.py::test_specific_behavior -v

# 2. Implement minimal code to make test pass
# 3. Run test to verify green
uv run pytest tests/test_new_feature.py::test_specific_behavior -v

# 4. Refactor while keeping tests green
uv run pytest tests/ --tb=short

# 5. Repeat for next behavior
```

**TDD with Background Tasks**:
```bash
# Start TDD task with explicit test-first instruction
.claude/ct start feature-tdd "Implement user authentication using strict TDD: 
1. Write failing test for login validation
2. Implement minimal code to pass
3. Write failing test for password hashing  
4. Implement minimal code to pass
5. Refactor and ensure all tests pass" --worktree

# Monitor and ensure TDD discipline
.claude/ct conversation feature-tdd
# Verify each commit follows Red→Green→Refactor pattern
```

**TDD Quality Checks**:
- Every task must include test creation BEFORE implementation
- No implementation without a failing test first
- All tests must pass before task completion
- Refactoring steps must maintain green tests

### Git Workflow with Worktrees

**Recommended Pattern for Feature Development**:
```bash
# 1. Start on feature branch (already created)
git checkout feature/my-feature

# 2. Create isolated worktree tasks for sub-components (TDD-focused)
.claude/ct start task1 "TDD implementation of component A: tests first, minimal implementation" --worktree
.claude/ct start task2 "TDD implementation of component B: tests first, minimal implementation" --worktree

# 3. Review TDD compliance and merge completed tasks
.claude/ct conversation task1  # Verify Red→Green→Refactor pattern
.claude/ct merge task1
.claude/ct remove task1

# 4. Run full test suite before PR
uv run pytest tests/ -v

# 5. Feature branch ready for main branch PR
```

**Benefits**:
- **Test-driven discipline**: Every feature starts with tests
- **Parallel TDD development**: Multiple components developed simultaneously with test coverage
- **Isolation**: Each task has its own git branch and working directory
- **Safe experimentation**: Worktree failures don't affect main development
- **Clean history**: Each task creates focused commits that follow TDD pattern
- **Quality assurance**: Tests ensure functionality before merge

### Implementation Notes

- **Tool restrictions**: Currently disabled to ensure basic functionality; can be re-enabled later for security
- **Monitoring**: Background processes monitor task completion and update conversation history
- **JSON output**: Tasks use `--output-format json` for structured response parsing
- **Absolute paths**: Handles directory changes properly for cross-project task execution

## Target Success Metrics

- **Reliability**: 99.9% success rate on valid operations
- **Safety**: Zero false positives in conflict detection  
- **Performance**: <2s response time for typical operations
- **LLM Success**: AI can execute multi-step refactoring workflows