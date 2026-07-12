---
name: refactoring-patterns
description: "Code refactoring guidelines: YAGNI-first approach, safe incremental changes, test-backed refactoring, and common Django/DRF patterns."
---

# Refactoring Patterns

## Usage
Use this skill when refactoring existing code. Prioritize deletion over addition, incremental over big-bang, test-backed over risky.

## Steps
1. Verify tests exist or write them first
2. Take `git diff` snapshot — confirm what will change
3. One concern per commit (rename OR extract OR simplify — not all)
4. Run tests after each change — if tests fail, code is wrong not tests
5. Commit with `refactor(scope): description`

## Rules
- **YAGNI first** — ask "does this need to exist?" before any refactoring
- **One change per commit** — never mix refactor with feature/fix
- **Behavior must not change** — refactoring = structure change, not behavior change
- **Revertable** — branch or stash before large changes
- **Small merges** — small PRs > one giant PR
- **Halt if no tests** — do not refactor untested code without writing tests first

## Priority Order
1. Delete dead code, unused files, unnecessary dependencies
2. Simplify — early returns, guard clauses over nested ifs
3. Extract — functions over ~30 lines into smaller units
4. Rename — unclear names to descriptive ones
5. DRY — only for real duplication, not coincidental similarity

## Anti-Patterns (Do NOT refactor when)
- Before a deadline if risky
- No tests exist and cannot write them
- Only "looks better" without readability/performance gain