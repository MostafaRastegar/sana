---
name: semantic-commits
description: "Git operations: semantic commits with conventional commit format, auto-generated messages from code changes."
---

# Semantic Commits

## Usage
Use this skill for any Git commit/push workflow. Ensures consistent conventional commit format.

## Steps
1. Detect modified files in working directory
2. Generate semantic commit message from code changes
3. Stage modified files
4. Commit with generated message

## Rules
- Commit message must be `lower_snake_case`
- Format: `type(scope): description`
- Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `style`, `ci`

## Extended Format
For complex changes, use the full conventional commit structure:

```
type(scope): description

[optional body — one sentence per change, wrap at 72 chars]

[optional footer: BREAKING CHANGE: <description> or REF: #issue]
```

- **Breaking changes**: append `!` after type/scope: `feat(api)!: remove deprecated v1 endpoint`
- **Body**: use when description alone is insufficient. Explain *why*, not *what*.
- **Footers**: `BREAKING CHANGE:`, `Refs: #123`, `Closes #456`

## Scope Examples
- `feat(auth):` — auth-related feature
- `fix(serializer):` — serializer fix
- `refactor(views):` — view refactor
- `perf(query):` — query optimization
- `test(models):` — model tests
- `ci(docker):` — CI/CD changes
- `docs(api):` — API documentation