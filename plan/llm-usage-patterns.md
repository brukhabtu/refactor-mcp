# LLM Usage Patterns

Common patterns and workflows for LLMs working with refactor-mcp documentation and codebase.

## Discovery Workflow

### Starting a New Session
```bash
# 1. Get oriented (ALWAYS start here)
cat CLAUDE.md

# 2. Understand the project
cat plan/project-plan.md

# 3. Check current implementation status  
find refactor_mcp/ -name "*.py"
ls tests/

# 4. Read relevant specs based on your task
cat plan/[specific-area].md
```

### Before Implementing Anything
```bash
# Check what already exists
find . -name "*[keyword]*" -type f
grep -r "ClassName\|function_name" refactor_mcp/

# Read the spec
cat plan/[relevant-spec].md

# Check current tests
find tests/ -name "*test*" | head -5
```

## Task-Specific Patterns

### Provider Implementation
```bash
# Required reading
cat plan/core-architecture.md      # Provider interface
cat plan/rope-provider.md          # Implementation example
cat plan/design-principles.md      # Error handling patterns

# Check existing
ls refactor_mcp/providers/
cat refactor_mcp/providers/base.py  # If exists
```

### MCP Tool Development  
```bash
# Required reading
cat plan/mcp-interface.md          # Tool specifications
cat plan/data-models.md            # Request/response models

# Check existing
ls refactor_mcp/server/
cat refactor_mcp/server/mcp_server.py  # If exists
```

### CLI Command Development
```bash
# Required reading  
cat plan/cli-interface.md          # Command specifications
cat plan/interface-design.md       # Error handling patterns

# Check existing
ls refactor_mcp/cli/
uv run python -m refactor_mcp.cli --help  # Current state
```

### Data Model Changes
```bash
# Required reading
cat plan/data-models.md            # All model definitions
cat plan/design-principles.md      # Validation patterns

# Check existing
ls refactor_mcp/models/
find . -name "*model*" -o -name "*param*" -o -name "*response*"
```

## Anti-Duplicate Checks

### Before Creating New Files
```bash
# Check if similar functionality exists
find . -name "*[similar-keyword]*"
grep -r "similar_function" refactor_mcp/

# Check plan documentation  
grep -r "similar concept" plan/
```

### Before Adding New Commands
```bash
# Check existing CLI
uv run python -m refactor_mcp.cli --help
cat plan/cli-interface.md

# Check existing MCP tools
cat plan/mcp-interface.md
grep "@mcp.tool" refactor_mcp/ -r
```

### Before Adding New Models
```bash
# Check existing models
cat plan/data-models.md
find refactor_mcp/ -name "*model*" -o -name "*param*" -o -name "*response*"
```

## Implementation Patterns

### Following Existing Conventions
```bash
# Check naming patterns
ls refactor_mcp/                   # Module names
grep "class.*:" refactor_mcp/ -r   # Class naming
grep "def.*:" refactor_mcp/ -r     # Function naming
```

### Error Handling Consistency
```bash
# Check existing error patterns
cat plan/design-principles.md      # Error philosophy
grep -r "ErrorResponse\|error_type" refactor_mcp/
cat refactor_mcp/models/errors.py  # If exists
```

### Testing Patterns
```bash
# Check existing test structure
find tests/ -name "test_*.py" | head -5
cat tests/conftest.py              # If exists
grep -r "def test_" tests/ | head -10
```

## Documentation Update Patterns

### When Adding New Concepts
1. Check if concept fits in existing plan file
2. If new file needed, follow `kebab-case.md` naming
3. Update `plan/README.md` navigation
4. Update `CLAUDE.md` quick reference

### When Implementation Differs from Plan
1. Update plan documentation first
2. Note changes in implementation commits
3. Keep plan and code in sync

## Efficiency Tips

### Use Glob Patterns for Quick Discovery
```bash
find . -name "*rope*" -o -name "*provider*"      # Provider-related
find . -name "*mcp*" -o -name "*server*"         # MCP-related  
find . -name "*cli*" -o -name "*command*"        # CLI-related
find . -name "*test*" -type f                    # All tests
```

### Use Grep for Concept Discovery  
```bash
grep -r "RefactoringProvider" .                  # Provider usage
grep -r "@mcp.tool" .                            # MCP tools
grep -r "BaseModel" .                            # Pydantic models
grep -r "def test_" tests/                       # Test functions
```

### Quick Status Checks
```bash
wc -l refactor_mcp/**/*.py          # Code size
find refactor_mcp/ -name "*.py" | wc -l    # File count
git status                          # Working state
uv run pytest tests/ --tb=short     # Test status
```

This pattern-based approach ensures LLMs can quickly orient themselves and avoid duplicating existing work while following established project conventions.