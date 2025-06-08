#!/bin/bash

# Development startup script following Claude Code best practices
# Usage: ./dev-start.sh [feature-name]

set -e

FEATURE_NAME=${1:-"patch-$(date +%s)"}

echo "🚀 Starting development for: $FEATURE_NAME"
echo "📋 Following Claude Code best practices..."

# Step 1: Create worktree
echo "1. Creating worktree..."
./gw.sh "$FEATURE_NAME"

# Get the worktree path
WORKTREE_PATH="../refactor-mcp-bruk-habtu-$FEATURE_NAME"

# Step 2: Setup environment
echo "2. Setting up environment in worktree..."
cd "$WORKTREE_PATH"
uv sync

# Step 3: Run initial health check
echo "3. Running initial health check..."
uv run pytest tests/ --tb=short || echo "⚠️  Some tests failing (this might be expected for new features)"

# Step 4: Show current state
echo "4. Current project state:"
echo "   📁 Worktree: $PWD"
echo "   🔧 Python: $(uv run python --version)"
echo "   📦 Dependencies: $(uv run pip list | wc -l) packages"

# Step 5: Development guidance
echo ""
echo "🎯 Development guidance:"
echo "   1. Read existing code first: Read tool on relevant files"
echo "   2. Write failing test as target"
echo "   3. Implement minimal solution"
echo "   4. Run: uv run pytest tests/ -v"
echo "   5. Quality check: uv run ruff check . && uv run mypy refactor_mcp/"
echo ""
echo "💡 VS Code tasks available:"
echo "   - Ctrl+Shift+P → Tasks: Run Task → test"
echo "   - Ctrl+Shift+P → Tasks: Run Task → quality"
echo "   - Ctrl+Shift+P → Tasks: Run Task → dev-cycle"
echo ""
echo "Ready for development! 🎉"