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