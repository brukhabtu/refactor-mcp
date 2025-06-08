# Claude Code Automation Scripts

This directory contains headless mode and multi-Claude automation tools following Claude Code best practices.

## Scripts Overview

### `claude-headless.sh` - Headless Mode Automation
Programmatic Claude integration for CI/CD and automation workflows.

**Commands:**
```bash
# Issue triage (GitHub automation)
./scripts/claude-headless.sh triage "Bug: App crashes" "Detailed issue description"

# Code review automation  
./scripts/claude-headless.sh review "$(git diff --name-only)"

# Large-scale migrations
./scripts/claude-headless.sh migrate "*.py" "Add type hints to all functions"

# Subjective linting
./scripts/claude-headless.sh lint refactor_mcp/core/

# Test generation
./scripts/claude-headless.sh test refactor_mcp/core/provider.py
```

### `multi-claude.sh` - Multi-Claude Workflows
Coordinate multiple Claude instances for parallel development.

**Commands:**
```bash
# Parallel development (multiple worktrees)
./scripts/multi-claude.sh parallel foundation "core interfaces" "rope provider" "cli commands"

# Code review workflow (separate implementation and review)
./scripts/multi-claude.sh review symbol-analysis

# Fan-out automation (large-scale changes)
./scripts/multi-claude.sh fanout "Add docstrings" "*.py"
```

## Integration Points

### GitHub Actions (`.github/workflows/claude-automation.yml`)
- **Issue Triage**: Automatically labels and triages new GitHub issues
- **PR Review**: Provides subjective code review on pull requests  
- **Daily Linting**: Runs periodic code quality checks

### Development Workflow
These scripts integrate with the existing development tools:
- Works with `gw.sh`/`gwr.sh` worktree management
- Uses `.clauderc` project configuration
- Follows `DEVELOPMENT_TARGETS.md` goals
- Respects `CLAUDE.md` guidelines

## Usage Patterns

### 1. Issue Triage Automation
```bash
# Triggered by GitHub webhook or manually
./scripts/claude-headless.sh triage "$ISSUE_TITLE" "$ISSUE_BODY"
# Returns JSON with suggested labels and rationale
```

### 2. Multi-Agent Code Review
```bash
# Setup separate worktrees for implementation and review
./scripts/multi-claude.sh review my-feature

# Terminal 1: Implementation Claude
cd ../refactor-mcp-bruk-habtu-my-feature-implementation
claude

# Terminal 2: Review Claude  
cd ../refactor-mcp-bruk-habtu-my-feature-review
claude
```

### 3. Large-Scale Migrations
```bash
# Example: Add logging to all modules
./scripts/claude-headless.sh migrate "refactor_mcp/**/*.py" "Add logging import and logger setup to each module"

# Example: Standardize error handling
./scripts/multi-claude.sh fanout "Replace bare except clauses with specific exceptions" "*.py"
```

### 4. Continuous Quality
```bash
# Daily linting (automated via GitHub Actions)
./scripts/claude-headless.sh lint

# Pre-commit review
git diff --name-only | xargs ./scripts/claude-headless.sh review
```

## Configuration

### Environment Variables
- `ANTHROPIC_API_KEY` - Required for Claude API access
- `CLAUDE_MODEL` - Optional model selection

### Dependencies
- `claude` CLI tool installed and configured
- `jq` for JSON processing
- `git` for repository operations

## Best Practices

### Headless Mode
1. **Use streaming JSON**: `--output-format stream-json` for structured output
2. **Limit tool access**: `--allowedTools Edit,Read` for safety
3. **Set timeouts**: Prevent hanging operations
4. **Handle failures**: Graceful degradation when Claude is unavailable

### Multi-Claude Coordination
1. **Separate contexts**: Use different worktrees for different roles
2. **Clear task definitions**: Specific objectives for each Claude instance
3. **Coordination files**: Shared status and communication files
4. **Regular syncing**: Merge completed work promptly

### Error Handling
1. **Validate inputs**: Check file existence, git state, etc.
2. **Graceful failures**: Continue processing other tasks if one fails
3. **Detailed logging**: Track what worked and what didn't
4. **Recovery mechanisms**: Ability to retry failed operations

## Examples

### Setting Up Parallel Foundation Development
```bash
# Create 4 parallel worktrees for foundation work
./scripts/multi-claude.sh parallel foundation \
  "Provider interface design" \
  "Rope provider implementation" \
  "CLI command structure" \
  "Basic MCP server setup"

# This creates:
# ../refactor-mcp-bruk-habtu-foundation-task-1/ - Provider interface
# ../refactor-mcp-bruk-habtu-foundation-task-2/ - Rope implementation  
# ../refactor-mcp-bruk-habtu-foundation-task-3/ - CLI structure
# ../refactor-mcp-bruk-habtu-foundation-task-4/ - MCP server

# Open 4 terminals, navigate to each, start Claude with specific tasks
```

### Automated Code Review Pipeline
```bash
# When PR is created, automatically review
changed_files=$(git diff origin/main..HEAD --name-only)
./scripts/claude-headless.sh review "$changed_files" | \
  jq '.issues[] | select(.type == "bug")' > critical-issues.json

# If critical issues found, block merge
if [ -s critical-issues.json ]; then
  echo "Critical issues found, blocking merge"
  exit 1
fi
```

## Troubleshooting

### Common Issues
1. **Claude CLI not found**: Install with `curl -fsSL https://claude.ai/install.sh | sh`
2. **API key missing**: Set `ANTHROPIC_API_KEY` environment variable
3. **Permission errors**: Ensure scripts are executable (`chmod +x`)
4. **Git worktree conflicts**: Clean up with `./gwr.sh` before starting new work

### Debugging
- Use `--verbose` flag with Claude for detailed logging
- Check script output files (e.g., `review-output.json`)
- Monitor `PARALLEL_DEV_STATUS.md` for coordination status
- Verify worktree status with `git worktree list`