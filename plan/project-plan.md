# Refactor MCP - Project Plan & Scope

## Project Overview

**refactor-mcp** is the first AST refactoring engine designed specifically for LLM consumption. It provides reliable, safe Python code refactoring operations through the Model Context Protocol (MCP), enabling AI systems to execute sophisticated refactoring workflows autonomously.

## Problem Statement

Current state: LLMs excel at identifying what needs refactoring but are terrible at executing it safely.

- Text-based refactoring is error-prone and misses edge cases
- Pattern matching fails with complex Python semantics (scope, imports, inheritance)
- No conflict detection or rollback mechanisms
- Manual verification required for every change

Our solution: Industrial-grade AST refactoring with AI-optimized interfaces.

## Core Value Proposition

We're building the bridge between AI refactoring intelligence and safe execution:

- **LLMs provide strategy**: "Extract lines 45-67 into a validate_input method"
- **Our tools provide execution**: Safe AST manipulation with conflict detection
- **Result**: AI can confidently execute complex refactoring without breaking code

## Target Platform

**Primary**: Claude Code (MCP-native environment)
**Secondary**: Any MCP-compatible AI system

## Architecture Philosophy

### Pluggable Provider System

- **Phase 1**: Rope provider (Python expertise, battle-tested)
- **Phase 2**: Tree-sitter provider (multi-language breadth)
- **Phase 3**: Specialized providers (rust-analyzer, LibCST, etc.)

### Dual Interface Pattern

- **MCP Server**: AI-optimized tool interface
- **CLI Interface**: Testing, debugging, development workflow

### Explicit-First Design

- No hidden state or implicit context
- Predictable behavior for LLM interactions
- Clear error messages with actionable suggestions

## MVP Scope (Phase 1)

### Core Refactoring Operations

1. **Symbol Analysis** - Get symbol information (definition, type, scope)
2. **Symbol Renaming** - Safe cross-codebase symbol renaming with conflict detection
3. **Method Extraction** - Extract code regions into new methods (named functions first)
4. **Reference Finding** - Locate all symbol usages across project
5. **Anonymous Element Discovery** - Find and extract lambdas, expressions, code blocks

### Interface Design Principles

- **Symbol-first operations**: Use qualified names (`auth.utils.login`) rather than positions
- **On-demand discovery**: `show` command reveals extractable elements when needed
- **Auto-generated IDs**: Stable references for anonymous elements (`function.lambda_1`)
- **Discovery-driven workflow**: Find → analyze → refactor patterns
- **Explicit disambiguation**: No hidden state, clear error messages with suggestions

### Technology Stack

- **Core Engine**: Python Rope library
- **Interface Framework**: FastMCP with Pydantic validation
- **CLI Framework**: Python Click
- **Type System**: Pydantic BaseModel throughout
- **Testing**: pytest with provider mocking

## Success Metrics

### Technical Metrics

- **Reliability**: 99.9% success rate on valid operations
- **Safety**: Zero false positives in conflict detection
- **Performance**: <2s response time for typical operations

### User Experience Metrics

- **LLM Success Rate**: AI can execute multi-step refactoring workflows
- **Error Recovery**: Clear guidance when operations fail
- **Discovery Efficiency**: Find target symbols/code in <3 commands

## Risk Mitigation

### Technical Risks

- **Rope limitations**: Start Python-only, expand incrementally
- **Position accuracy**: Provide discovery tools for LLMs
- **Complex codebases**: Implement robust error handling and timeouts

### Product Risks

- **Market validation**: Focus on Python community first
- **Scope creep**: Strict MVP boundaries, resist feature bloat
- **Tool complexity**: Prioritize simple, predictable interfaces

## Future Expansion Strategy

### Phase 2: Multi-Language Foundation

- Tree-sitter provider for JavaScript, Rust, Elixir, Go
- Unified interface across all providers
- Language-specific optimizations where available

### Phase 3: Advanced Capabilities

- rust-analyzer provider for sophisticated Rust refactoring
- Semgrep provider for pattern-based transformations
- LibCST provider for Python formatting-aware refactoring

### Phase 4: Ecosystem Integration

- Git integration for change tracking
- IDE plugins for direct integration
- CI/CD workflow automation

## Competitive Positioning

**Not competing with**:

- GitHub Copilot (creative suggestions)
- IDE refactoring tools (human-oriented interfaces)
- General code transformation tools

**Creating new category**:

- **AI-executable refactoring**: Tools designed for programmatic consumption
- **Safety-first automation**: Guaranteed behavior preservation
- **Protocol-standardized**: MCP as the interface standard

## Development Timeline

### Week 1-2: Foundation

- Provider interface design
- Rope provider core implementation
- Basic MCP server setup

### Week 3-4: Core Operations

- Implement all 5 MVP operations
- CLI interface development
- Comprehensive testing framework

### Week 5-6: Polish & Documentation

- Error handling and edge cases
- Documentation and examples
- Performance optimization

### Week 7-8: Validation

- Real-world testing with Claude Code
- Community feedback integration
- Release preparation

## Long-term Vision

**refactor-mcp** becomes the standard for AI-driven code refactoring:

- Universal AST manipulation protocol for AI systems
- Multi-language support through best-of-breed providers
- Foundation for autonomous software engineering workflows

The future where AI can safely execute sophisticated refactoring operations starts with solving Python refactoring extremely well.
