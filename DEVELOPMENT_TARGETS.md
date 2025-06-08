# Development Targets - Clear Goals for Claude Code

This file provides concrete, testable targets for development following Claude Code best practices.

## Phase 1: Foundation (Current Priority)

### Target 1: Basic Provider Interface
**Goal**: Create a working provider interface that Claude can iterate against

**Success Criteria**:
```python
# This should work:
from refactor_mcp.core.provider import RefactorProvider, SymbolInfo

provider = RopeProvider()
result = provider.analyze_symbol("mymodule.function")
assert isinstance(result, SymbolInfo)
assert result.qualified_name == "mymodule.function"
```

**Files to create/modify**:
- `refactor_mcp/core/provider.py` - Abstract base class
- `refactor_mcp/providers/rope_provider.py` - Concrete implementation
- `tests/unit/test_provider_interface.py` - Test target

### Target 2: CLI Symbol Analysis
**Goal**: Basic CLI command that works with real Python files

**Success Criteria**:
```bash
# This should work:
echo "def hello(): pass" > test.py
uv run python -m refactor_mcp.cli analyze test.hello
# Should output: Symbol 'test.hello' found at test.py:1
```

**Files to create/modify**:
- `refactor_mcp/cli/__main__.py` - CLI entry point
- `refactor_mcp/cli/commands.py` - Command implementations
- `tests/integration/test_cli_basic.py` - Integration test

### Target 3: Symbol Renaming
**Goal**: Safe symbol renaming with backup

**Success Criteria**:
```bash
# This should work:
echo "def old_name(): pass\nold_name()" > test.py
uv run python -m refactor_mcp.cli rename test.old_name new_name
# Should rename function and call, create backup
```

## Phase 2: Core Operations

### Target 4: Method Extraction
**Visual Target**: Extract this lambda into a named function
```python
# Before:
users = [user for user in all_users if lambda u: u.age >= 18 and u.verified]

# After:
def is_adult_verified(user):
    return user.age >= 18 and user.verified

users = [user for user in all_users if is_adult_verified(user)]
```

### Target 5: Reference Finding
**Visual Target**: Find all usages across project
```bash
uv run python -m refactor_mcp.cli find UserService.validate
# Should list:
# auth/service.py:15 - Definition
# auth/service.py:42 - Call in login()  
# tests/test_auth.py:23 - Test usage
```

## Phase 3: Advanced Features

### Target 6: Anonymous Element Discovery
**Visual Target**: Show extractable elements in a function
```bash
uv run python -m refactor_mcp.cli show "auth.login"
# Should output:
# Extractable elements in auth.login:
# - lambda_1: Line 15 - Email validation lambda
# - expr_1: Line 22 - Complex query expression
# - block_1: Lines 30-35 - Error handling block
```

### Target 7: MCP Server Integration
**Goal**: Working MCP server for Claude Code

**Success Criteria**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "refactor_analyze_symbol",
    "arguments": {"symbol": "mymodule.function"}
  }
}
```

## Development Workflow for Each Target

1. **Explore First**: Read existing code to understand patterns
2. **Write Failing Test**: Create concrete test that defines success
3. **Implement Minimally**: Write just enough code to pass the test
4. **Verify Visually**: Test with real Python files, not just unit tests
5. **Iterate**: Refine based on edge cases and real-world usage

## Testing Against Real Codebases

Create test projects for validation:
```bash
mkdir test-projects
cd test-projects

# Simple project
mkdir simple-project
cd simple-project
echo "def calculate(x, y): return x + y" > math_utils.py
echo "from math_utils import calculate; print(calculate(1, 2))" > main.py

# Test our tool
cd ../..
uv run python -m refactor_mcp.cli analyze test-projects/simple-project/math_utils.calculate
```

## Success Metrics

Each phase should achieve:
- ✅ All tests pass
- ✅ Works with real Python files (not just unit tests)
- ✅ Proper error handling and user feedback
- ✅ Follows established patterns in codebase
- ✅ Documentation updated

## Visual Feedback

For CLI commands, aim for clear, helpful output:
```
✅ Symbol 'math_utils.calculate' analyzed successfully
📍 Location: test-projects/simple-project/math_utils.py:1:0
🔍 Type: function
📦 Module: math_utils
🏷️  Parameters: x, y
📝 Docstring: None
🔗 References: 1 found
```