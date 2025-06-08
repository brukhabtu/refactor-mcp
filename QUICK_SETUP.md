# 🚀 Quick Setup Guide

Get your refactor-mcp project ready for development in 5 minutes.

## Prerequisites

```bash
# Install required tools
brew install gh uv  # GitHub CLI and UV package manager

# Authenticate with GitHub
gh auth login

# Clone and setup project
git clone <your-repo-url>
cd refactor-mcp
uv sync
```

## 1. Automated Security Setup

```bash
# Run the complete security setup
./scripts/setup-github-security.sh

# This will:
# ✅ Set up API key as GitHub secret
# ✅ Enable branch protection  
# ✅ Configure security features
# ✅ Create automation labels
# ✅ Set up repository settings
```

## 2. Manual API Key Setup (Alternative)

```bash
# If you prefer manual setup
./scripts/github-secrets.sh set

# List secrets to verify
./scripts/github-secrets.sh list
```

## 3. Start Development

```bash
# Guided development setup
./dev-start.sh foundation

# Or manual worktree creation
./gw.sh my-feature
```

## 4. Test Automation

```bash
# Test headless mode
./scripts/claude-headless.sh lint

# Test multi-Claude setup  
./scripts/multi-claude.sh parallel test "task1" "task2"

# Verify security
./verify-changes.sh
```

## 5. Key Commands Reference

```bash
# Development workflow
./dev-start.sh <feature>     # Start new feature
./verify-changes.sh          # Review changes
./gwr.sh                     # Clean up worktrees

# Automation
./scripts/claude-headless.sh triage "title" "body"  # Issue triage
./scripts/claude-headless.sh review "$(git diff --name-only)"  # Code review
./scripts/multi-claude.sh review my-feature  # Multi-agent review

# Security management
./scripts/github-secrets.sh rotate           # Rotate API key
./scripts/github-secrets.sh list            # List secrets
./scripts/setup-github-security.sh --help   # Security options
```

## 6. Verify Setup

**Check GitHub repository:**
- Go to Settings → Secrets and variables → Actions
- Verify `ANTHROPIC_API_KEY` is set
- Check Settings → Branches for protection rules
- Review Settings → Security & analysis features

**Test locally:**
```bash
# Run quality checks
uv run pytest tests/ --tb=short
uv run ruff check . && uv run mypy refactor_mcp/

# Test CLI (when implemented)
uv run python -m refactor_mcp.cli --help
```

## Troubleshooting

**GitHub CLI not authenticated:**
```bash
gh auth status
gh auth login
```

**API key issues:**
```bash
# Test API key
./scripts/github-secrets.sh test

# Rotate if needed
./scripts/github-secrets.sh rotate
```

**Permission errors:**
```bash
# Fix script permissions
chmod +x *.sh scripts/*.sh

# Check repository permissions
gh repo view --json permissions
```

**Workflow failures:**
```bash
# Check workflow status
gh run list

# View specific run
gh run view <run-id>
```

## Next Steps

1. **Read the docs**: Check `DEVELOPMENT_TARGETS.md` for specific goals
2. **Start coding**: Use `./dev-start.sh foundation` to begin
3. **Follow TDD**: Write tests first, implement after
4. **Use automation**: Let Claude help with reviews and quality checks
5. **Stay secure**: Rotate API keys quarterly

## Help & Documentation

- **`CLAUDE.md`** - Claude Code guidance and project overview
- **`DEVELOPMENT_TARGETS.md`** - Concrete development goals
- **`GIT_WORKFLOW.md`** - Multi-agent git workflow
- **`SECURITY.md`** - Security best practices
- **`scripts/README.md`** - Automation script documentation

Happy coding! 🎉