#!/bin/bash

# Multi-agent verification script
# Run this to have a "second Claude" verify changes

set -e

echo "🔍 Multi-Agent Verification"
echo "=========================="

# Check if we're in a worktree
if [[ $(git rev-parse --show-toplevel) != *"refactor-mcp"* ]]; then
    echo "❌ Run this from within a refactor-mcp worktree"
    exit 1
fi

echo "📁 Current worktree: $(basename $PWD)"
echo "🌿 Current branch: $(git branch --show-current)"
echo ""

# 1. Code quality checks
echo "1. Code Quality Checks"
echo "----------------------"
uv run ruff check . || echo "❌ Ruff issues found"
uv run mypy refactor_mcp/ || echo "❌ Type issues found"
echo "✅ Code quality checks complete"
echo ""

# 2. Test verification
echo "2. Test Verification" 
echo "-------------------"
uv run pytest tests/ -v || echo "❌ Some tests failed"
echo ""

# 3. Architecture compliance
echo "3. Architecture Compliance"
echo "-------------------------"
echo "Checking against CLAUDE.md patterns..."

# Check for proper imports
echo -n "  - Pydantic models used: "
if grep -r "from pydantic import" refactor_mcp/ > /dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️ Consider using Pydantic models"
fi

# Check for logging
echo -n "  - Logging implemented: "
if grep -r "get_logger" refactor_mcp/ > /dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️ Consider adding logging"
fi

# Check for error handling
echo -n "  - Error handling present: "
if grep -r "try:" refactor_mcp/ > /dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️ Consider adding error handling"
fi

echo ""

# 4. Integration test suggestion
echo "4. Integration Test"
echo "------------------"
echo "Test CLI commands manually:"
echo "  uv run python -m refactor_mcp.cli --help"
echo "  uv run python -m refactor_mcp.cli analyze some.symbol"
echo ""

# 5. Commit readiness
echo "5. Commit Readiness"
echo "------------------"
if git diff --quiet && git diff --cached --quiet; then
    echo "⚠️ No changes to commit"
else
    echo "📝 Changes ready for commit:"
    git status --porcelain
    echo ""
    echo "Suggested commit workflow:"
    echo "  git add ."
    echo "  git commit -m 'Implement [feature]: [description]'"
    echo "  git push origin $(git branch --show-current)"
fi

echo ""
echo "🎉 Verification complete!"