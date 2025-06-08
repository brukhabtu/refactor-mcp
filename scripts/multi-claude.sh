#!/bin/bash

# Multi-Claude workflow automation
# Implements the patterns from Claude Code best practices

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RESET='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${RESET} $1"
}

success() {
    echo -e "${GREEN}✅ $1${RESET}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${RESET}"
}

# Setup multiple worktrees for parallel Claude development
setup_parallel_development() {
    local base_name="$1"
    local tasks=("$@")
    
    cd "$PROJECT_ROOT"
    
    log "Setting up parallel development environment"
    log "Base name: $base_name"
    
    # Create worktrees for each task
    for i in "${!tasks[@]}"; do
        local task="${tasks[$i]}"
        local worktree_name="${base_name}-task-$((i+1))"
        local branch_name="bruk.habtu/${worktree_name}"
        
        log "Creating worktree for: $task"
        
        # Create worktree
        ./gw.sh "$worktree_name" > /dev/null 2>&1
        
        # Create task file in worktree
        local worktree_path="../refactor-mcp-bruk-habtu-${worktree_name}"
        cat > "${worktree_path}/TASK.md" << EOF
# Task: $task

## Objective
$task

## Context
This is part of a multi-Claude parallel development workflow.

## Development Guidelines
1. Focus only on this specific task
2. Follow patterns from CLAUDE.md
3. Write tests first (TDD approach)  
4. Use the verify-changes.sh script before committing
5. Check DEVELOPMENT_TARGETS.md for concrete goals

## Completion Criteria
- [ ] Tests pass
- [ ] Code quality checks pass
- [ ] Task objective achieved
- [ ] Documentation updated if needed

## Getting Started
Run these commands in this worktree:
\`\`\`bash
uv sync
uv run pytest tests/ --tb=short
# Start development...
\`\`\`
EOF
        
        success "Created worktree: $worktree_path"
        echo "    Task: $task"
        echo "    Branch: $branch_name"
        echo ""
    done
    
    # Create coordination file
    cat > "PARALLEL_DEV_STATUS.md" << EOF
# Parallel Development Status

Started: $(date)
Base name: $base_name

## Active Worktrees

EOF
    
    for i in "${!tasks[@]}"; do
        local task="${tasks[$i]}"
        local worktree_name="${base_name}-task-$((i+1))"
        cat >> "PARALLEL_DEV_STATUS.md" << EOF
### Task $((i+1)): $worktree_name
- **Objective**: $task
- **Status**: 🔄 In Progress
- **Worktree**: ../refactor-mcp-bruk-habtu-${worktree_name}/
- **Branch**: bruk.habtu/${worktree_name}

EOF
    done
    
    cat >> "PARALLEL_DEV_STATUS.md" << EOF

## Instructions

1. Open each worktree in a separate terminal tab:
$(for i in "${!tasks[@]}"; do
    local worktree_name="${base_name}-task-$((i+1))"
    echo "   \`cd ../refactor-mcp-bruk-habtu-${worktree_name}\`"
done)

2. Start Claude in each worktree:
   \`claude\`

3. Monitor progress and approve permission requests as needed

4. When tasks complete, merge back to main:
   \`git checkout main && git merge bruk.habtu/worktree-name\`

5. Clean up completed worktrees:
   \`./gwr.sh\`
EOF
    
    log "Parallel development environment ready!"
    echo ""
    echo "Next steps:"
    echo "1. Open $(echo "${tasks[@]}" | wc -w) terminal tabs"
    echo "2. Navigate to each worktree and start Claude"
    echo "3. Check PARALLEL_DEV_STATUS.md for coordination"
}

# Code-review workflow (one Claude writes, another reviews)
code_review_workflow() {
    local feature_name="$1"
    
    log "Setting up code-review workflow for: $feature_name"
    
    # Create worktrees
    ./gw.sh "${feature_name}-implementation"
    ./gw.sh "${feature_name}-review"
    
    # Setup implementation worktree
    local impl_path="../refactor-mcp-bruk-habtu-${feature_name}-implementation"
    cat > "${impl_path}/IMPLEMENTATION_TASK.md" << EOF
# Implementation Task: $feature_name

## Role: Implementation Claude

Your job is to implement the feature according to specifications.

## Guidelines:
1. Focus purely on implementation
2. Write code that works
3. Follow TDD approach
4. Don't worry about perfect code review - that's handled separately
5. Create clear commit messages

## Process:
1. Read DEVELOPMENT_TARGETS.md for concrete goals
2. Write failing tests first
3. Implement minimal code to pass tests
4. Commit changes with descriptive messages
5. Move to next requirement

## Output:
When complete, create a summary in IMPLEMENTATION_SUMMARY.md
EOF
    
    # Setup review worktree  
    local review_path="../refactor-mcp-bruk-habtu-${feature_name}-review"
    cat > "${review_path}/REVIEW_TASK.md" << EOF
# Review Task: $feature_name

## Role: Review Claude

Your job is to review implementation from the implementation worktree.

## Guidelines:
1. Focus on code quality, not implementation
2. Look for bugs, edge cases, style issues
3. Check adherence to project standards
4. Suggest improvements
5. Don't implement - just review

## Process:
1. Read implementation from: $impl_path
2. Run tests and quality checks
3. Analyze code for issues
4. Create detailed review feedback
5. Suggest specific improvements

## Output:
Create REVIEW_FEEDBACK.md with findings and suggestions
EOF
    
    success "Code-review workflow ready!"
    echo "Implementation worktree: $impl_path"
    echo "Review worktree: $review_path"
}

# Fan-out automation for large tasks
fanout_automation() {
    local task_description="$1"
    local pattern="$2"
    
    log "Setting up fan-out automation"
    log "Task: $task_description"
    log "Pattern: $pattern"
    
    # First, have Claude generate the task list
    local task_list=$(claude -p "
Generate a task list for this automation:

Task: $task_description
File pattern: $pattern
Project structure: $(find refactor_mcp/ -name '*.py' | head -20)

Create a JSON array of specific files or modules that need this change:
{
  \"tasks\": [
    {\"file\": \"path/to/file.py\", \"description\": \"specific change needed\"},
    ...
  ]
}

Return only the JSON, no other text.
" --output-format stream-json)
    
    echo "$task_list" > "automation-tasks.json"
    
    # Process tasks with headless Claude
    python3 - << EOF
import json
import subprocess
import sys

with open('automation-tasks.json', 'r') as f:
    data = json.load(f)

total = len(data['tasks'])
success_count = 0
failed_tasks = []

print(f"Processing {total} automation tasks...")

for i, task in enumerate(data['tasks'], 1):
    print(f"[{i}/{total}] Processing: {task['file']}")
    
    try:
        result = subprocess.run([
            'claude', '-p', f"""
Apply this change: {task['description']}
File: {task['file']}

Requirements:
1. Make the change safely
2. Maintain functionality  
3. Follow project coding standards
4. Return ONLY 'OK' if successful, 'FAIL' if failed

Do not return any other text.
            """,
            '--allowedTools', 'Edit,Read'
        ], capture_output=True, text=True, timeout=60)
        
        if 'OK' in result.stdout:
            success_count += 1
            print(f"  ✅ Success")
        else:
            failed_tasks.append(task)
            print(f"  ❌ Failed")
            
    except Exception as e:
        failed_tasks.append(task)
        print(f"  ❌ Error: {e}")

print(f"\nAutomation complete: {success_count}/{total} succeeded")
if failed_tasks:
    print("Failed tasks:")
    for task in failed_tasks:
        print(f"  - {task['file']}: {task['description']}")
EOF
    
    success "Fan-out automation complete!"
}

# Main command dispatcher
main() {
    case "$1" in
        "parallel")
            shift
            local base_name="$1"
            shift
            setup_parallel_development "$base_name" "$@"
            ;;
        "review")
            if [ $# -lt 2 ]; then
                echo "Usage: $0 review <feature_name>"
                exit 1
            fi
            code_review_workflow "$2"
            ;;
        "fanout")
            if [ $# -lt 3 ]; then
                echo "Usage: $0 fanout \"<task_description>\" \"<file_pattern>\""
                exit 1
            fi
            fanout_automation "$2" "$3"
            ;;
        *)
            echo "Multi-Claude Workflow Automation"
            echo ""
            echo "Usage: $0 <command> [args...]"
            echo ""
            echo "Commands:"
            echo "  parallel <base_name> <task1> <task2> ...  - Setup parallel development"
            echo "  review <feature_name>                     - Setup code review workflow"
            echo "  fanout \"<task>\" \"<pattern>\"               - Fan-out automation"
            echo ""
            echo "Examples:"
            echo "  $0 parallel foundation \"core interfaces\" \"rope provider\" \"cli commands\""
            echo "  $0 review symbol-analysis"
            echo "  $0 fanout \"Add type hints\" \"*.py\""
            ;;
    esac
}

main "$@"