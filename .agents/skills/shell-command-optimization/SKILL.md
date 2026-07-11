---
name: shell-command-optimization
description: Token-efficient CLI commands using RTK proxy. Prefix all shell commands with `rtk` for token compression.
---

# Shell Command Optimization (RTK)

## When to Use
Use this skill when executing any CLI command (git, npm, docker, grep, etc.) to minimize token consumption via the `rtk` proxy.

## Rule
Always prefix shell commands with `rtk`:
```bash
rtk git status
rtk cargo test
rtk ls src/
rtk grep "pattern" src/
rtk docker ps
rtk gh pr list
```

## Meta Commands
```bash
rtk gain              # Show token savings
rtk gain --history    # Command history with savings
rtk discover          # Find missed RTK opportunities
rtk proxy <cmd>       # Run raw (no filtering, for debugging)