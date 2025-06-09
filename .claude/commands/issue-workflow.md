Please orchestrate a complete parallel development workflow for GitHub issue: $ARGUMENTS

Follow this comprehensive workflow:

## 1. Issue Analysis & Task Breakdown
1. Use `gh issue view $ARGUMENTS` to get the complete issue details
2. Analyze the acceptance criteria and identify independent work streams
3. Break the issue into 2-4 parallel tasks that don't overlap in file modifications
4. Ensure each task follows TDD principles (Red→Green→Refactor)

## 2. Launch Parallel Tasks with ct
For each identified task:
1. Use `.claude/ct start <task-name> "<detailed-context>" --worktree` 
2. Provide comprehensive context including:
   - Issue number and context
   - Specific acceptance criteria for this task
   - Files/components this task should focus on
   - TDD requirements (write failing tests first)
   - Integration requirements with other tasks

## 3. Active Task Management
1. Use `.claude/ct watch` to monitor all tasks in real-time
2. When tasks complete (status changes to response_received):
   - Use `.claude/ct conversation <task-name>` to review the work
   - Check if TDD was followed properly (Red→Green→Refactor)
   - Verify acceptance criteria were met
   - Look for integration issues or missing edge cases

## 4. Quality Assurance Loop
For each completed task:
1. Use `.claude/ct continue <task-name> "Review feedback: [specific issues found]"`
2. Request fixes for:
   - Missing test coverage
   - TDD violations  
   - Integration problems
   - Code quality issues
   - Acceptance criteria gaps
3. Repeat until the task meets all quality standards

## 5. Integration & Merge
1. Once all tasks pass review, merge them using `.claude/ct merge <task-name>`
2. Run full test suite to ensure integration works: `uv run pytest tests/ -v`
3. Run quality checks: `uv run ruff check . && uv run ruff format . && uv run mypy refactor_mcp/`
4. Create commit for the completed issue

## 6. Issue Completion
1. Update issue status or add completion comment
2. Ensure all acceptance criteria are met
3. Document any architectural decisions made during implementation

## Key Principles
- **TDD First**: Every task must write failing tests before implementation
- **Parallel Isolation**: Tasks should not modify the same files
- **Active Review**: Don't just launch tasks - actively review and improve them
- **Quality Gates**: All tests must pass, code must be clean
- **Integration Testing**: Verify tasks work together as a cohesive solution

Remember: This is not "fire and forget" - actively manage the tasks through to completion with multiple review cycles.