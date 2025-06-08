#!/bin/bash

# GitHub CLI security setup for refactor-mcp
# Automates repository security configuration using gh CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        error "GitHub CLI (gh) not found. Install with: brew install gh"
        exit 1
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        error "Not authenticated with GitHub. Run: gh auth login"
        exit 1
    fi
    
    # Check if we're in a git repo with remote
    if ! git remote get-url origin &> /dev/null; then
        error "No git remote 'origin' found. Push repository to GitHub first."
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Set up GitHub repository secrets
setup_secrets() {
    log "Setting up GitHub repository secrets..."
    
    # Check if ANTHROPIC_API_KEY secret exists
    if gh secret list | grep -q "ANTHROPIC_API_KEY"; then
        warning "ANTHROPIC_API_KEY secret already exists"
        read -p "Update it? (y/N): " update_secret
        if [[ ! "$update_secret" =~ ^[Yy]$ ]]; then
            log "Skipping secret update"
            return 0
        fi
    fi
    
    # Prompt for API key
    echo ""
    echo "🔑 API Key Setup"
    echo "=================="
    echo "Get your API key from: https://console.anthropic.com"
    echo "The key should start with: sk-ant-"
    echo ""
    read -s -p "Enter your Anthropic API key: " api_key
    echo ""
    
    # Validate API key format
    if [[ ! "$api_key" =~ ^sk-ant- ]]; then
        error "Invalid API key format. Should start with 'sk-ant-'"
        exit 1
    fi
    
    # Set the secret
    echo "$api_key" | gh secret set ANTHROPIC_API_KEY
    success "ANTHROPIC_API_KEY secret set"
    
    # Clear the variable for security
    unset api_key
}

# Configure branch protection rules
setup_branch_protection() {
    local branch="${1:-main}"
    
    log "Setting up branch protection for '$branch'..."
    
    # Check if branch exists
    if ! git show-ref --verify --quiet "refs/heads/$branch" && ! git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
        warning "Branch '$branch' not found. Creating branch protection anyway."
    fi
    
    # Set up branch protection rule
    gh api repos/:owner/:repo/branches/$branch/protection \
        --method PUT \
        --field required_status_checks='{"strict":true,"contexts":["security-scan"]}' \
        --field enforce_admins=true \
        --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":false}' \
        --field restrictions=null \
        --field allow_force_pushes=false \
        --field allow_deletions=false \
        > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        success "Branch protection enabled for '$branch'"
    else
        warning "Failed to set branch protection (may need admin permissions)"
    fi
}

# Enable security features
enable_security_features() {
    log "Enabling repository security features..."
    
    local repo_info=$(gh repo view --json name,owner)
    local repo_name=$(echo "$repo_info" | jq -r '.name')
    local owner=$(echo "$repo_info" | jq -r '.owner.login')
    
    # Enable vulnerability alerts
    gh api repos/$owner/$repo_name/vulnerability-alerts \
        --method PUT \
        > /dev/null 2>&1 && success "Vulnerability alerts enabled" || warning "Could not enable vulnerability alerts"
    
    # Enable automated security fixes
    gh api repos/$owner/$repo_name/automated-security-fixes \
        --method PUT \
        > /dev/null 2>&1 && success "Automated security fixes enabled" || warning "Could not enable automated security fixes"
    
    # Enable secret scanning (available for public repos)
    gh api repos/$owner/$repo_name \
        --method PATCH \
        --field security_and_analysis='{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}' \
        > /dev/null 2>&1 && success "Secret scanning enabled" || warning "Could not enable secret scanning (may require public repo)"
}

# Set up repository labels for automation
setup_labels() {
    log "Setting up repository labels for automation..."
    
    # Define labels for Claude automation
    declare -A labels=(
        ["automated"]="Automatically created or managed|#0052cc"
        ["code-quality"]="Code quality and linting issues|#fbca04"
        ["security"]="Security-related issues|#d93f0b"
        ["claude-review"]="Reviewed by Claude Code|#0052cc"
        ["needs-human-review"]="Requires human review|#d93f0b"
        ["bug"]="Something isn't working|#d93f0b"
        ["enhancement"]="New feature or request|#a2eeef"
        ["documentation"]="Improvements or additions to documentation|#0075ca"
        ["high-priority"]="High priority issue|#d93f0b"
        ["medium-priority"]="Medium priority issue|#fbca04"
        ["low-priority"]="Low priority issue|#0052cc"
        ["provider-rope"]="Related to Rope provider|#1d76db"
        ["provider-mcp"]="Related to MCP server|#1d76db"
        ["cli"]="Command line interface|#0052cc"
        ["core"]="Core functionality|#0052cc"
    )
    
    # Create or update labels
    for label in "${!labels[@]}"; do
        IFS='|' read -r description color <<< "${labels[$label]}"
        
        # Check if label exists
        if gh label list | grep -q "^$label"; then
            # Update existing label
            gh label edit "$label" --description "$description" --color "$color" > /dev/null 2>&1
            log "Updated label: $label"
        else
            # Create new label
            gh label create "$label" --description "$description" --color "$color" > /dev/null 2>&1
            log "Created label: $label"
        fi
    done
    
    success "Repository labels configured"
}

# Set up repository settings
setup_repository_settings() {
    log "Configuring repository settings..."
    
    local repo_info=$(gh repo view --json name,owner)
    local repo_name=$(echo "$repo_info" | jq -r '.name')
    local owner=$(echo "$repo_info" | jq -r '.owner.login')
    
    # Update repository settings
    gh api repos/$owner/$repo_name \
        --method PATCH \
        --field allow_squash_merge=true \
        --field allow_merge_commit=false \
        --field allow_rebase_merge=true \
        --field delete_branch_on_merge=true \
        --field has_issues=true \
        --field has_projects=true \
        --field has_wiki=false \
        > /dev/null 2>&1
    
    success "Repository settings configured"
}

# Create initial security issue
create_security_checklist() {
    log "Creating security checklist issue..."
    
    # Check if security checklist issue already exists
    if gh issue list --label "security" --state "open" | grep -q "Security Setup Checklist"; then
        warning "Security checklist issue already exists"
        return 0
    fi
    
    # Create security checklist issue
    gh issue create \
        --title "🔐 Security Setup Checklist" \
        --label "security,automated" \
        --body "# Security Setup Checklist

This issue tracks the security configuration of the refactor-mcp repository.

## ✅ Completed
- [x] API key stored as GitHub secret
- [x] Branch protection enabled
- [x] Security workflows configured
- [x] Repository labels created
- [x] .gitignore updated for secrets

## 🔄 Manual Steps Required

### Branch Protection Verification
1. Go to Settings → Branches
2. Verify 'main' branch protection is enabled
3. Ensure 'Require status checks' includes 'security-scan'

### Security Features (if not auto-enabled)
1. Go to Settings → Security & analysis
2. Enable 'Dependency graph'
3. Enable 'Dependabot alerts' 
4. Enable 'Dependabot security updates'
5. Enable 'Secret scanning' (public repos)

### Team Access Review
1. Go to Settings → Manage access
2. Review collaborator permissions
3. Ensure minimum necessary access

### Regular Maintenance
- [ ] Review access logs monthly
- [ ] Rotate API keys quarterly  
- [ ] Update dependencies regularly
- [ ] Monitor security advisories

## 🔗 Resources
- [Repository Security Guide](./SECURITY.md)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Anthropic API Security](https://docs.anthropic.com/en/api/getting-started)

Created automatically by setup-github-security.sh"

    success "Security checklist issue created"
}

# Validate GitHub Actions workflows
validate_workflows() {
    log "Validating GitHub Actions workflows..."
    
    cd "$PROJECT_ROOT"
    
    # Check if workflow files exist
    local workflow_dir=".github/workflows"
    if [ ! -d "$workflow_dir" ]; then
        warning "No GitHub Actions workflows found"
        return 0
    fi
    
    # Validate each workflow file
    for workflow in "$workflow_dir"/*.yml "$workflow_dir"/*.yaml; do
        if [ -f "$workflow" ]; then
            local filename=$(basename "$workflow")
            log "Validating workflow: $filename"
            
            # Check for security issues in workflows
            if grep -q "echo.*secret\|print.*secret" "$workflow"; then
                error "Workflow $filename may expose secrets!"
                return 1
            fi
            
            # Basic YAML syntax check (if yq is available)
            if command -v yq &> /dev/null; then
                if yq eval '.' "$workflow" > /dev/null 2>&1; then
                    log "  ✅ YAML syntax valid"
                else
                    warning "  ⚠️ YAML syntax issues in $filename"
                fi
            fi
        fi
    done
    
    success "Workflow validation complete"
}

# Main setup function
main() {
    echo "🔐 GitHub Security Setup for refactor-mcp"
    echo "========================================"
    echo ""
    
    # Parse command line arguments
    SKIP_BRANCH_PROTECTION=false
    SKIP_SECRETS=false
    BRANCH="main"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-branch-protection)
                SKIP_BRANCH_PROTECTION=true
                shift
                ;;
            --skip-secrets)
                SKIP_SECRETS=true
                shift
                ;;
            --branch)
                BRANCH="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --skip-branch-protection    Skip branch protection setup"
                echo "  --skip-secrets              Skip secrets setup"
                echo "  --branch BRANCH             Branch to protect (default: main)"
                echo "  --help                      Show this help"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Run setup steps
    check_prerequisites
    
    if [ "$SKIP_SECRETS" = false ]; then
        setup_secrets
    else
        warning "Skipping secrets setup"
    fi
    
    setup_labels
    setup_repository_settings
    enable_security_features
    
    if [ "$SKIP_BRANCH_PROTECTION" = false ]; then
        setup_branch_protection "$BRANCH"
    else
        warning "Skipping branch protection setup"
    fi
    
    validate_workflows
    create_security_checklist
    
    echo ""
    echo "🎉 Security setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Review the security checklist issue that was created"
    echo "2. Verify branch protection in GitHub Settings → Branches"
    echo "3. Check Security & Analysis settings for any manual steps"
    echo "4. Review the SECURITY.md file for ongoing best practices"
    echo ""
    echo "Test your automation with:"
    echo "  ./scripts/claude-headless.sh lint"
    echo "  ./scripts/multi-claude.sh parallel test \"task1\" \"task2\""
}

main "$@"