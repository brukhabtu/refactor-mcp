#!/bin/bash

# Git Worktree script
# Creates a new git worktree with a branch and opens it in VS Code Insider

# Function to display help
show_help() {
    echo "Usage: $(basename $0) [OPTIONS] [branch-suffix]"
    echo ""
    echo "Creates a new git worktree with a branch and opens it in VS Code Insider."
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help      Show this help message"
    echo "  -m, --mcp       Select and activate an MCP configuration template"
    echo "  --mcp PURPOSE   Activate a specific MCP template (e.g., --mcp dwh)"
    echo ""
    echo "ARGUMENTS:"
    echo "  branch-suffix   Optional branch name suffix (default: patch-{timestamp})"
    echo ""
    echo "Available MCP templates:"
    
    # Dynamically list MCP templates from the directory
    local templates_dir="$MAIN_WORKTREE/mcp-json-templates"
    if [ -d "$templates_dir" ]; then
        for template in "$templates_dir"/.mcp.*.json; do
            if [ -f "$template" ]; then
                local template_name=$(basename "$template" | sed 's/^\.mcp\.//' | sed 's/\.json$//')
                echo -n "  - $template_name"
                
                # Extract description from README.md if available
                local readme="$templates_dir/README.md"
                if [ -f "$readme" ]; then
                    local desc=$(grep -A1 "\.mcp\.$template_name\.json" "$readme" | tail -n1 | sed 's/^[[:space:]]*//')
                    if [ -n "$desc" ] && [ "$desc" != "$(grep "\.mcp\.$template_name\.json" "$readme")" ]; then
                        echo ": $desc"
                    else
                        echo ""
                    fi
                else
                    echo ""
                fi
            fi
        done
    fi
    echo ""
    echo "Examples:"
    echo "  $(basename $0)                    # Create worktree with auto-generated branch name"
    echo "  $(basename $0) fix-bug            # Create worktree with branch tadasant/fix-bug"
    echo "  $(basename $0) --mcp dwh fix-bug  # Create worktree and activate dwh MCP template"
    echo "  $(basename $0) -m                 # Interactive MCP template selection"
}

# Function to select MCP template interactively
select_mcp_template() {
    local templates_dir="$1"
    local templates=()
    local descriptions=()
    
    # Collect available templates
    for template in "$templates_dir"/.mcp.*.json; do
        if [ -f "$template" ]; then
            local template_name=$(basename "$template" | sed 's/^\.mcp\.//' | sed 's/\.json$//')
            templates+=("$template_name")
            
            # Get description from README if available
            local readme="$templates_dir/README.md"
            local desc=""
            if [ -f "$readme" ]; then
                desc=$(grep -A1 "\.mcp\.$template_name\.json" "$readme" | tail -n1 | sed 's/^[[:space:]]*//')
                if [ -z "$desc" ] || [ "$desc" = "$(grep "\.mcp\.$template_name\.json" "$readme")" ]; then
                    desc="No description available"
                fi
            else
                desc="No description available"
            fi
            descriptions+=("$desc")
        fi
    done
    
    if [ ${#templates[@]} -eq 0 ]; then
        echo "No MCP templates found in $templates_dir"
        return 1
    fi
    
    # Always use numbered selection for simplicity and reliability
    echo "Available MCP templates:" >&2
    echo "" >&2
    for i in "${!templates[@]}"; do
        echo "  $((i+1)). ${templates[$i]}" >&2
        echo "     ${descriptions[$i]}" >&2
        echo "" >&2
    done
    
    read -p "Select template (1-${#templates[@]}): " selection
    
    if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le ${#templates[@]} ]; then
        echo "${templates[$((selection-1))]}"
    else
        echo "Invalid selection" >&2
        return 1
    fi
}

# Function to activate MCP template
activate_mcp_template() {
    local template_name="$1"
    local worktree_path="$2"
    local templates_dir="$MAIN_WORKTREE/mcp-json-templates"
    
    local template_file="$templates_dir/.mcp.$template_name.json"
    if [ ! -f "$template_file" ]; then
        echo "Error: MCP template '$template_name' not found"
        return 1
    fi
    
    echo "Activating MCP template: $template_name"
    cp "$template_file" "$worktree_path/.mcp.json"
    echo "  ✓ Copied .mcp.$template_name.json to .mcp.json"
}

# Get the git repository root (works in both main repo and worktrees)
CURRENT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$CURRENT_ROOT" ]; then
  echo "Error: Not in a git repository"
  exit 1
fi

# Find the main worktree (the actual git directory)
GIT_COMMON_DIR="$(git rev-parse --git-common-dir 2>/dev/null)"
if [ "$GIT_COMMON_DIR" = ".git" ] || [ "$GIT_COMMON_DIR" = "$(pwd)/.git" ]; then
  # We're in the main repository
  MAIN_WORKTREE="$CURRENT_ROOT"
else
  # We're in a worktree, find the main worktree
  MAIN_WORKTREE="$(dirname "$GIT_COMMON_DIR")"
fi

# Parse command line arguments
MCP_TEMPLATE=""
BRANCH_SUFFIX=""
INTERACTIVE_MCP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -m)
            INTERACTIVE_MCP=true
            shift
            ;;
        --mcp)
            if [ -n "$2" ] && [[ ! "$2" =~ ^- ]]; then
                MCP_TEMPLATE="$2"
                shift 2
            else
                echo "Error: --mcp requires a template name"
                exit 1
            fi
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
        *)
            BRANCH_SUFFIX="$1"
            shift
            ;;
    esac
done

# Handle interactive MCP selection
if [ "$INTERACTIVE_MCP" = true ]; then
    MCP_TEMPLATE=$(select_mcp_template "$MAIN_WORKTREE/mcp-json-templates")
    if [ $? -ne 0 ] || [ -z "$MCP_TEMPLATE" ]; then
        echo "MCP template selection cancelled or failed"
        exit 1
    fi
fi

# If no argument provided, use patch-{datetime}
if [ -z "$BRANCH_SUFFIX" ]; then
  BRANCH_SUFFIX="patch-$(date +%s)"
fi

# Create the full branch name with github username prefix
BRANCH_NAME="tadasant/$BRANCH_SUFFIX"

# Create worktree directory name (replace / with -)
WORKTREE_DIR=$(echo "$BRANCH_NAME" | tr '/' '-')

# Stash any uncommitted changes
echo "Checking for uncommitted changes..."
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Stashing uncommitted changes..."
  git stash push -m "Auto-stash before creating worktree $BRANCH_NAME"
  STASHED=true
else
  STASHED=false
fi

# Ensure we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "Switching to main branch..."
  git checkout main
fi

# Pull latest main branch
echo "Pulling latest main branch..."
git pull origin main

# Create the worktree (at the same level as other worktrees)
echo "Creating worktree: $WORKTREE_DIR"
echo "With branch: $BRANCH_NAME"

# Get the parent directory of the main worktree
WORKTREES_PARENT="$(dirname "$MAIN_WORKTREE")"
NEW_WORKTREE_PATH="$WORKTREES_PARENT/$WORKTREE_DIR"

git worktree add "$NEW_WORKTREE_PATH" -b "$BRANCH_NAME"

if [ $? -eq 0 ]; then
  echo "Worktree created successfully!"
  
  # Copy Rails credential key files and VS Code tasks if they exist
  echo "Copying Rails credential keys and VS Code settings..."
  
  # Define the files to copy
  FILES_TO_COPY=(
    "web-app/config/master.key"
    "web-app/config/credentials/development.key"
    "web-app/config/credentials/production.key"
    "web-app/config/credentials/staging.key"
    ".vscode/tasks.json"
    "mcp-json-templates/.secrets"
  )
  
  # Copy each file if it exists (from current worktree)
  for FILE in "${FILES_TO_COPY[@]}"; do
    SOURCE_FILE="$CURRENT_ROOT/$FILE"
    if [ -f "$SOURCE_FILE" ]; then
      TARGET_FILE="$NEW_WORKTREE_PATH/$FILE"
      TARGET_DIR=$(dirname "$TARGET_FILE")
      
      # Create target directory if it doesn't exist
      mkdir -p "$TARGET_DIR"
      
      # Copy the file
      cp "$SOURCE_FILE" "$TARGET_FILE"
      echo "  ✓ Copied $FILE"
    else
      echo "  ⚠ $FILE not found in source directory"
    fi
  done
  
  # Handle MCP template activation if requested
  if [ -n "$MCP_TEMPLATE" ]; then
    activate_mcp_template "$MCP_TEMPLATE" "$NEW_WORKTREE_PATH"
  fi
  
  echo "Opening in VS Code Insider..."
  code-insiders "$NEW_WORKTREE_PATH" --new-window
  
  # If we stashed changes, apply them back on main
  if [ "$STASHED" = true ]; then
    echo "Returning to original location and applying stashed changes..."
    cd "$CURRENT_ROOT"
    git stash pop
  fi
else
  echo "Failed to create worktree"
  exit 1
fi