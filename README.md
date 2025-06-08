# refactor-mcp

AST refactoring engine designed for LLM consumption through Model Context Protocol (MCP).

## Quick Start

```bash
# Guided development setup (recommended)
./dev-start.sh foundation

# Manual setup
git clone <repo>
cd refactor-mcp
uv sync
uv run pytest tests/ --tb=short
```

## Documentation Structure

### Project Design & Planning
- **`plan/project-plan.md`** - Overall project scope and objectives
- **`plan/architecture.md`** - System architecture and design decisions  
- **`plan/interface-design.md`** - API and interface specifications
- **`plan/implementation-plan.md`** - Development phases and implementation strategy

### Development Workflow
- **`CLAUDE.md`** - Claude Code guidance and project overview
- **`DEVELOPMENT_TARGETS.md`** - Concrete, testable development goals  
- **`GIT_WORKFLOW.md`** - Multi-agent git worktree workflow
- **`.clauderc`** - Claude Code configuration and commands
- **`.vscode/`** - VS Code tasks and settings

## Key Tools

### Development Workflow
- **`./gw.sh`** - Create git worktrees for parallel development
- **`./gwr.sh`** - Interactive worktree cleanup
- **`./dev-start.sh`** - Guided development startup
- **`./verify-changes.sh`** - Multi-agent verification

### Claude Code Automation
- **`./scripts/claude-headless.sh`** - Headless mode automation (CI/CD, linting, migrations)
- **`./scripts/multi-claude.sh`** - Multi-Claude workflows (parallel development, code review)
- **`./scripts/setup-github-security.sh`** - Automated GitHub security setup via gh CLI
- **`./scripts/github-secrets.sh`** - GitHub secrets management and rotation
- **`.github/workflows/claude-automation.yml`** - GitHub Actions integration

## Architecture

Symbol-first refactoring operations through pluggable providers:
- **Providers**: Rope (Python), Tree-sitter, rust-analyzer
- **Interfaces**: CLI + MCP server
- **Operations**: Analyze, rename, extract, find references

See `CLAUDE.md` for full architecture details.