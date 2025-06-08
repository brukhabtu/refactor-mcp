#!/bin/bash

# Claude Code headless automation harness for refactor-mcp
# Usage: ./scripts/claude-headless.sh <command> [args...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure we're in project root
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

error() {
    echo -e "${RED}❌ $1${RESET}"
}

# Check if claude command is available
check_claude() {
    if ! command -v claude &> /dev/null; then
        error "Claude Code CLI not found. Please install it first."
        exit 1
    fi
}

# Issue triage automation
triage_issue() {
    local issue_body="$1"
    local issue_title="$2"
    
    log "Triaging issue: $issue_title"
    
    # Create temporary file with issue content
    local temp_file=$(mktemp)
    cat > "$temp_file" << EOF
Issue Title: $issue_title

Issue Body:
$issue_body

Project Context:
$(cat CLAUDE.md | head -50)
EOF
    
    # Run Claude in headless mode for triage
    local result=$(claude -p "
Analyze this GitHub issue for the refactor-mcp project and suggest appropriate labels.

Consider these label categories:
- Type: bug, feature, enhancement, documentation, question
- Priority: high, medium, low  
- Component: cli, mcp-server, rope-provider, core, testing
- Status: needs-triage, needs-reproduction, ready-for-work

Return only a JSON object with suggested labels and a brief rationale:
{
  \"labels\": [\"label1\", \"label2\"],
  \"rationale\": \"Brief explanation\"
}
" --output-format stream-json < "$temp_file")
    
    rm "$temp_file"
    echo "$result"
}

# Code review automation
review_code() {
    local files_changed="$1"
    
    log "Running Claude code review on changed files"
    
    # Create context file
    local temp_file=$(mktemp)
    cat > "$temp_file" << EOF
Files changed in this PR:
$files_changed

Project coding standards:
$(cat .clauderc)

Recent git diff:
$(git diff HEAD~1..HEAD)
EOF
    
    # Run Claude review
    local review=$(claude -p "
Review this code change for the refactor-mcp project.

Focus on:
1. Code quality and style adherence
2. Potential bugs or edge cases
3. Documentation needs
4. Test coverage
5. Architecture alignment with project goals

Provide actionable feedback in JSON format:
{
  \"issues\": [
    {\"type\": \"bug|style|docs|test\", \"file\": \"path\", \"line\": 123, \"message\": \"description\"}
  ],
  \"suggestions\": [\"improvement suggestions\"],
  \"approval\": true|false
}
" --output-format stream-json < "$temp_file")
    
    rm "$temp_file"
    echo "$review"
}

# Migration automation (for large-scale changes)
migrate_files() {
    local pattern="$1"
    local transformation="$2"
    
    log "Starting migration: $transformation"
    
    # Find files matching pattern
    local files=$(find refactor_mcp/ -name "$pattern" -type f)
    local total=$(echo "$files" | wc -l)
    local success_count=0
    local fail_count=0
    
    log "Found $total files to migrate"
    
    # Process each file
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            log "Migrating: $file"
            
            local result=$(claude -p "
Apply this transformation to the given Python file: $transformation

File path: $file
File content:
$(cat "$file")

Requirements:
1. Apply the transformation safely
2. Maintain code functionality
3. Follow project coding standards from .clauderc
4. Return only 'OK' if successful, 'FAIL' if failed

Return ONLY 'OK' or 'FAIL' - no other text.
" --allowedTools Edit,Read 2>/dev/null)
            
            if [[ "$result" =~ "OK" ]]; then
                success "Migrated $file"
                ((success_count++))
            else
                error "Failed to migrate $file"
                ((fail_count++))
            fi
        fi
    done <<< "$files"
    
    log "Migration complete: $success_count succeeded, $fail_count failed"
}

# Linting with Claude (subjective review)
claude_lint() {
    local target_dir="${1:-refactor_mcp/}"
    
    log "Running Claude subjective linting on $target_dir"
    
    # Get recent changes or all files
    local files
    if git diff --quiet HEAD~1..HEAD; then
        files=$(find "$target_dir" -name "*.py" -type f | head -10)
    else
        files=$(git diff --name-only HEAD~1..HEAD | grep "\.py$" || echo "")
    fi
    
    if [ -z "$files" ]; then
        warning "No Python files to lint"
        return 0
    fi
    
    # Create context for Claude
    local temp_file=$(mktemp)
    cat > "$temp_file" << EOF
Linting target: $target_dir
Project standards: $(cat .clauderc | grep -A 20 "style:")

Files to review:
EOF
    
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            echo "=== $file ===" >> "$temp_file"
            cat "$file" >> "$temp_file"
            echo "" >> "$temp_file"
        fi
    done <<< "$files"
    
    # Run Claude linting
    local result=$(claude -p "
Perform subjective code review on these Python files, focusing on:

1. Misleading function/variable names
2. Stale or incorrect comments
3. Typos in strings and comments
4. Code clarity and readability
5. Inconsistencies with project style

Return findings in JSON format:
{
  \"issues\": [
    {\"file\": \"path\", \"line\": 123, \"type\": \"naming|comment|typo|clarity\", \"message\": \"description\", \"suggestion\": \"fix\"}
  ],
  \"summary\": \"Overall assessment\"
}
" --output-format stream-json < "$temp_file")
    
    rm "$temp_file"
    echo "$result"
}

# Test generation
generate_tests() {
    local module="$1"
    
    log "Generating tests for module: $module"
    
    if [ ! -f "$module" ]; then
        error "Module file not found: $module"
        return 1
    fi
    
    local result=$(claude -p "
Generate comprehensive tests for this Python module.

Module: $module
Content:
$(cat "$module")

Requirements:
1. Use pytest framework
2. Follow existing test patterns in tests/
3. Include edge cases and error conditions
4. Use descriptive test names
5. Add docstrings for complex tests

Create test file and return 'OK' if successful, 'FAIL' if failed.
" --allowedTools Write,Read,Edit)
    
    echo "$result"
}

# Main command dispatcher
main() {
    check_claude
    
    case "$1" in
        "triage")
            if [ $# -lt 3 ]; then
                error "Usage: $0 triage \"<issue_title>\" \"<issue_body>\""
                exit 1
            fi
            triage_issue "$3" "$2"
            ;;
        "review")
            review_code "$2"
            ;;
        "migrate")
            if [ $# -lt 3 ]; then
                error "Usage: $0 migrate \"<file_pattern>\" \"<transformation>\""
                exit 1
            fi
            migrate_files "$2" "$3"
            ;;
        "lint")
            claude_lint "$2"
            ;;
        "test")
            if [ $# -lt 2 ]; then
                error "Usage: $0 test <module_path>"
                exit 1
            fi
            generate_tests "$2"
            ;;
        *)
            echo "Claude Code Headless Automation for refactor-mcp"
            echo ""
            echo "Usage: $0 <command> [args...]"
            echo ""
            echo "Commands:"
            echo "  triage \"<title>\" \"<body>\"     - Triage GitHub issue"
            echo "  review [files]                   - Review code changes"
            echo "  migrate \"<pattern>\" \"<transform>\" - Bulk file migration"
            echo "  lint [directory]                 - Subjective code linting"
            echo "  test <module>                    - Generate tests for module"
            echo ""
            echo "Examples:"
            echo "  $0 triage \"Bug report\" \"App crashes on startup\""
            echo "  $0 review \"\$(git diff --name-only)\""
            echo "  $0 migrate \"*.py\" \"Add type hints to all functions\""
            echo "  $0 lint refactor_mcp/core/"
            echo "  $0 test refactor_mcp/core/provider.py"
            ;;
    esac
}

main "$@"