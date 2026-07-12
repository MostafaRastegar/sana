---
name: shell-command-optimization
description: ALL shell commands MUST be prefixed with `rtk` for token compression.
---

# Shell Command Optimization (RTK)

## Usage
- Every `execute_command` tool call
- Every CLI command execution

## Examples
- `rtk git status` (not `git status`)
- `rtk python manage.py test` (not `python manage.py test`)
- `rtk ls -la` (not `ls -la`)
- `rtk grep -r "pattern" src/` (not `grep -r "pattern" src/`)
- `rtk docker compose up` (not `docker compose up`)

## Meta Commands
- `rtk gain` — show token savings
- `rtk discover` — find missed optimization opportunities

## Exception
- Commands that pipe output to stdin of another command may not work with rtk prefix
- If rtk fails for a command, run without prefix as fallback
