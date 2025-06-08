#!/bin/bash

# GitHub secrets management using gh CLI
# Secure API key setup and rotation for Claude Code automation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# List all repository secrets
list_secrets() {
    log "Repository secrets:"
    gh secret list
}

# Set ANTHROPIC_API_KEY secret
set_api_key() {
    local api_key="$1"
    
    if [ -z "$api_key" ]; then
        echo ""
        echo "🔑 Anthropic API Key Setup"
        echo "=========================="
        echo "Get your API key from: https://console.anthropic.com"
        echo "The key should start with: sk-ant-"
        echo ""
        read -s -p "Enter your Anthropic API key: " api_key
        echo ""
    fi
    
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

# Rotate API key (update existing secret)
rotate_api_key() {
    log "Rotating ANTHROPIC_API_KEY..."
    
    # Check if secret exists
    if ! gh secret list | grep -q "ANTHROPIC_API_KEY"; then
        error "ANTHROPIC_API_KEY secret not found. Use 'set' command first."
        exit 1
    fi
    
    echo ""
    echo "🔄 API Key Rotation"
    echo "=================="
    echo "1. Generate a new API key at: https://console.anthropic.com"
    echo "2. Revoke the old key after setting the new one"
    echo ""
    
    set_api_key
    
    echo ""
    warning "Don't forget to revoke the old API key at https://console.anthropic.com"
}

# Set up additional secrets for automation
setup_automation_secrets() {
    log "Setting up additional automation secrets..."
    
    # GitHub token (for cross-repo operations)
    echo ""
    echo "🔑 GitHub Token (Optional)"
    echo "========================="
    echo "For cross-repository operations, you may need a GitHub token."
    echo "Generate at: https://github.com/settings/tokens"
    echo "Required scopes: repo, workflow"
    echo ""
    read -p "Set up GitHub token? (y/N): " setup_github_token
    
    if [[ "$setup_github_token" =~ ^[Yy]$ ]]; then
        read -s -p "Enter GitHub token (ghp_...): " github_token
        echo ""
        
        if [[ "$github_token" =~ ^ghp_ ]]; then
            echo "$github_token" | gh secret set GITHUB_TOKEN
            success "GITHUB_TOKEN secret set"
        else
            warning "Invalid GitHub token format. Skipping."
        fi
        unset github_token
    fi
    
    # Slack webhook (for notifications)
    echo ""
    echo "🔑 Slack Webhook (Optional)"  
    echo "=========================="
    echo "For automation notifications to Slack."
    echo ""
    read -p "Set up Slack webhook? (y/N): " setup_slack
    
    if [[ "$setup_slack" =~ ^[Yy]$ ]]; then
        read -p "Enter Slack webhook URL: " slack_webhook
        if [ -n "$slack_webhook" ]; then
            echo "$slack_webhook" | gh secret set SLACK_WEBHOOK_URL
            success "SLACK_WEBHOOK_URL secret set"
        fi
        unset slack_webhook
    fi
}

# Delete a secret
delete_secret() {
    local secret_name="$1"
    
    if [ -z "$secret_name" ]; then
        error "Secret name required"
        echo "Usage: $0 delete <secret_name>"
        exit 1
    fi
    
    # Confirm deletion
    echo ""
    warning "This will permanently delete the secret: $secret_name"
    read -p "Are you sure? (y/N): " confirm
    
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        gh secret delete "$secret_name"
        success "Secret '$secret_name' deleted"
    else
        log "Deletion cancelled"
    fi
}

# Test API key validity
test_api_key() {
    log "Testing ANTHROPIC_API_KEY..."
    
    # Check if secret exists
    if ! gh secret list | grep -q "ANTHROPIC_API_KEY"; then
        error "ANTHROPIC_API_KEY secret not found"
        exit 1
    fi
    
    # We can't directly access the secret value, but we can test it in a workflow
    echo ""
    echo "To test the API key, run:"
    echo "  ./scripts/claude-headless.sh lint"
    echo ""
    echo "Or trigger the GitHub Actions workflow manually:"
    echo "  gh workflow run claude-automation.yml"
}

# Show secret usage in workflows
show_usage() {
    log "Secret usage in GitHub Actions workflows:"
    echo ""
    
    # Find workflow files that use secrets
    if [ -d ".github/workflows" ]; then
        for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
            if [ -f "$workflow" ]; then
                local filename=$(basename "$workflow")
                local secrets_used=$(grep -o '\${{ secrets\.[A-Z_]* }}' "$workflow" 2>/dev/null | sort | uniq)
                
                if [ -n "$secrets_used" ]; then
                    echo "📄 $filename:"
                    echo "$secrets_used" | sed 's/^/  - /'
                    echo ""
                fi
            fi
        done
    else
        warning "No .github/workflows directory found"
    fi
    
    echo "💡 Tips:"
    echo "  - Secrets are encrypted and only accessible during workflow runs"
    echo "  - Never echo or log secret values in workflows"
    echo "  - Use secrets for API keys, tokens, and sensitive configuration"
    echo "  - Rotate secrets regularly (quarterly recommended)"
}

# Backup secrets configuration (names only, not values)
backup_secrets_config() {
    local backup_file="secrets-backup-$(date +%Y%m%d-%H%M%S).json"
    
    log "Creating secrets configuration backup..."
    
    # Get secret names and metadata (not values)
    gh secret list --json name,updated_at > "$backup_file"
    
    success "Secrets configuration backed up to: $backup_file"
    echo ""
    echo "📋 Backup contains:"
    cat "$backup_file" | jq '.[] | {name: .name, updated: .updated_at}'
}

# Import secrets from environment file
import_from_env() {
    local env_file="$1"
    
    if [ -z "$env_file" ]; then
        error "Environment file required"
        echo "Usage: $0 import <env_file>"
        exit 1
    fi
    
    if [ ! -f "$env_file" ]; then
        error "Environment file not found: $env_file"
        exit 1
    fi
    
    log "Importing secrets from: $env_file"
    
    # Read environment file and set secrets
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        if [[ "$key" =~ ^#.*$ ]] || [ -z "$key" ]; then
            continue
        fi
        
        # Remove quotes from value
        value=$(echo "$value" | sed 's/^["'\'']//' | sed 's/["'\'']*$//')
        
        if [ -n "$value" ]; then
            echo "$value" | gh secret set "$key"
            success "Set secret: $key"
        fi
    done < "$env_file"
    
    warning "Remember to delete the environment file for security: rm $env_file"
}

# Main command dispatcher
main() {
    case "$1" in
        "list"|"ls")
            list_secrets
            ;;
        "set")
            set_api_key "$2"
            ;;
        "rotate")
            rotate_api_key
            ;;
        "setup")
            setup_automation_secrets
            ;;
        "delete"|"remove"|"rm")
            delete_secret "$2"
            ;;
        "test")
            test_api_key
            ;;
        "usage")
            show_usage
            ;;
        "backup")
            backup_secrets_config
            ;;
        "import")
            import_from_env "$2"
            ;;
        *)
            echo "GitHub Secrets Management for refactor-mcp"
            echo ""
            echo "Usage: $0 <command> [args...]"
            echo ""
            echo "Commands:"
            echo "  list                    - List all repository secrets"
            echo "  set [api_key]          - Set ANTHROPIC_API_KEY secret"
            echo "  rotate                 - Rotate ANTHROPIC_API_KEY"
            echo "  setup                  - Set up additional automation secrets"
            echo "  delete <secret_name>   - Delete a secret"
            echo "  test                   - Test API key validity"
            echo "  usage                  - Show secret usage in workflows"
            echo "  backup                 - Backup secrets configuration"
            echo "  import <env_file>      - Import secrets from environment file"
            echo ""
            echo "Examples:"
            echo "  $0 set                        # Interactive API key setup"
            echo "  $0 set sk-ant-123...         # Set API key directly"
            echo "  $0 rotate                     # Rotate existing API key"
            echo "  $0 delete OLD_SECRET          # Delete specific secret"
            echo "  $0 import .env.secrets        # Import from file"
            echo ""
            echo "Security Notes:"
            echo "  - API keys are encrypted by GitHub"
            echo "  - Secrets are only accessible during workflow runs"
            echo "  - Rotate secrets regularly (quarterly recommended)"
            echo "  - Never commit secret values to git"
            ;;
    esac
}

main "$@"