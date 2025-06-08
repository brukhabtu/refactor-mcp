# Git Workflow for Multi-Agent Development

This document outlines the git workflow for the refactor-mcp project using the Agent Cluster methodology with git worktrees.

## Quick Start

```bash
# Create new worktree for development
./gw.sh feature-name

# Clean up merged worktrees
./gwr.sh
```

## Core Workflow

### 1. Starting New Work

```bash
# Create a new worktree for your feature
./gw.sh symbol-analysis          # Creates branch: bruk.habtu/symbol-analysis
./gw.sh fix-rope-edge-case      # Creates branch: bruk.habtu/fix-rope-edge-case

# The script will:
# - Create worktree in ../refactor-mcp-bruk-habtu-symbol-analysis/
# - Switch to new branch bruk.habtu/symbol-analysis
# - Copy credential files and VS Code settings
# - Open in VS Code Insiders
```

### 2. Development Cycle

```bash
# In your worktree directory
uv run pytest tests/ --tb=short    # TDD: Start with failing tests
# Implement functionality...
uv run ruff check . && uv run ruff format .  # Fix code quality
uv run mypy refactor_mcp/          # Fix type issues
uv run pytest tests/ -v            # Validate tests pass
```

### 3. Committing Changes

```bash
git add .
git commit -m "Implement symbol analysis for rope provider

- Add symbol resolution for qualified names
- Handle edge cases for nested scopes
- Add comprehensive test coverage"

git push origin bruk.habtu/symbol-analysis
```

### 4. Creating Pull Requests

```bash
# Create PR from command line
gh pr create --title "Add symbol analysis functionality" --body "
## Summary
- Implements core symbol analysis for rope provider
- Adds support for qualified name resolution
- Handles complex import scenarios

## Test plan
- ✅ Unit tests for symbol resolution
- ✅ Integration tests with real Python projects
- ✅ Edge case testing for nested scopes
"
```

### 5. Cleanup

```bash
# Interactive worktree cleanup
./gwr.sh

# Options:
# - Select merged PRs for cleanup
# - Select all non-main worktrees
# - Individual selection with space/enter
```

## Worktree Management Scripts

### gw.sh - Worktree Creation

**Features:**
- Auto-generates branch names with username prefix
- Copies credential files and settings
- Opens in VS Code Insiders
- Stashes/restores uncommitted changes
- MCP template support (optional)

**Usage:**
```bash
./gw.sh                        # Auto-generated branch name
./gw.sh my-feature            # Custom branch suffix
./gw.sh --help                # Show all options
```

### gwr.sh - Worktree Removal

**Features:**
- Interactive selection interface
- PR status checking via GitHub CLI
- Bulk operations (select all merged, etc.)
- Safe deletion with confirmation

**Controls:**
- `↑/↓` or `j/k`: Navigate
- `Space`: Select/deselect
- `d`: Delete selected
- `a`: Select all non-main
- `m`: Select all merged
- `q`: Quit

## Branch Naming Convention

```
bruk.habtu/feature-name
bruk.habtu/fix-bug-description
bruk.habtu/refactor-component
```

- Always prefixed with GitHub username
- Use kebab-case for feature names
- Be descriptive but concise

## Multi-Agent Coordination

### Phase-Based Development

```bash
# Phase 1: Foundation
./gw.sh foundation
cd ../refactor-mcp-bruk-habtu-foundation/
# Implement core interfaces, basic structure

# Phase 2: Rope Provider
./gw.sh rope-provider
cd ../refactor-mcp-bruk-habtu-rope-provider/
# Implement rope-specific functionality

# Phase 3: CLI Interface
./gw.sh cli-interface
cd ../refactor-mcp-bruk-habtu-cli-interface/
# Build command-line interface

# Phase 4: MCP Server
./gw.sh mcp-server
cd ../refactor-mcp-bruk-habtu-mcp-server/
# Implement MCP server layer
```

### Coordination Points

1. **Stable Interfaces**: Define clear APIs between components
2. **Regular Syncing**: Merge completed phases back to main
3. **Conflict Resolution**: Use `git rebase origin/main` in worktrees
4. **Documentation**: Update CLAUDE.md with architectural decisions

### Integration Workflow

```bash
# In each worktree, regularly sync with main
git fetch origin
git rebase origin/main

# When phase is complete
git checkout main
git merge bruk.habtu/foundation --no-ff
git push origin main

# Clean up completed worktree
./gwr.sh  # Select and delete merged worktree
```

## Testing Strategy

### TDD Development Cycle

```bash
# 1. Write failing tests
uv run pytest tests/ --tb=short

# 2. Implement minimal functionality
# Edit code...

# 3. Fix quality issues
uv run ruff check . && uv run ruff format .
uv run mypy refactor_mcp/

# 4. Validate tests pass
uv run pytest tests/ -v

# 5. Refactor and repeat
```

### Integration Testing

```bash
# Test CLI functionality
uv run python -m refactor_mcp.cli --help
uv run python -m refactor_mcp.cli analyze some.symbol

# Test with real codebases
mkdir test-projects
cd test-projects
git clone https://github.com/example/python-project
cd ..
uv run python -m refactor_mcp.cli rename test-projects/python-project/src/module.function new_function
```

## Safety Measures

### Backup Protocol

```bash
# Before any refactoring operation
uv run python -m refactor_mcp.cli backup src/

# If something goes wrong
uv run python -m refactor_mcp.cli restore backup-2024-01-15-14-30-22
```

### Pre-commit Validation

```bash
# Always run before committing
uv run ruff check . && uv run ruff format .
uv run mypy refactor_mcp/
uv run pytest tests/ -v

# Or use the VS Code task
# Ctrl+Shift+P -> Tasks: Run Task -> quality
```

## Troubleshooting

### Common Issues

**Worktree already exists:**
```bash
./gwr.sh  # Remove existing worktree first
./gw.sh same-name  # Try again
```

**VS Code Insiders not opening:**
```bash
# Check if VS Code Insiders is installed
which code-insiders

# Edit gw.sh to use regular VS Code
# Change: code-insiders "$NEW_WORKTREE_PATH" --new-window
# To: code "$NEW_WORKTREE_PATH" --new-window
```

**Git authentication issues:**
```bash
# Ensure GitHub CLI is authenticated
gh auth status
gh auth login
```

### Debugging

```bash
# Check worktree status
git worktree list

# Check branch status across worktrees
git log --oneline --graph --all

# Verify remote tracking
git branch -vv
```

## Best Practices

1. **One Feature Per Worktree**: Keep changes focused and atomic
2. **Regular Commits**: Commit frequently with descriptive messages
3. **Test-Driven**: Always start with failing tests
4. **Quality Gates**: Run linting and type checking before commits
5. **Documentation**: Update relevant docs with each change
6. **Clean History**: Use `git rebase -i` to clean up commits before merging
7. **Backup Before Refactoring**: Always create backups before major changes

## VS Code Integration

The worktree scripts automatically:
- Copy `.vscode/tasks.json` to new worktrees
- Set up Python environment configuration
- Enable automatic formatting with ruff
- Configure test discovery for pytest

**Available Tasks:**
- `setup`: Run `uv sync`
- `test`: Run full test suite
- `test-quick`: Run tests with short traceback
- `lint`: Run ruff check and format
- `typecheck`: Run mypy
- `quality`: Run all quality checks
- `dev-cycle`: Complete TDD cycle