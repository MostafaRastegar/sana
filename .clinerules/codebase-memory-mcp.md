# Codebase Memory Rules

## Indexing
- After major code changes or at session start, run `index_repository` on project path
- Mode: `moderate` for routine work, `full` for deep analysis, `fast` for quick checks

## Code Search
- Use `search_graph` INSTEAD OF grep/glob when finding definitions, implementations, or relationships
- Use `query_graph` for complex multi-hop patterns (callers of callers, cross-service traces)
- Use `trace_path` for impact analysis and dependency tracing
- Use `search_code` for text pattern search enriched with graph context

## When to Use
- Finding where a function is called: `trace_path` mode=calls
- Finding all callers of a function: `trace_path` mode=calls direction=inbound
- Understanding architecture: `get_architecture`
- Reading a function's source: `search_graph` first to find qualified_name, then `get_code_snippet`
- Finding code by natural language: `search_graph` query="user description"
- Finding semantic matches: `search_graph` semantic_query=["keyword1","keyword2"]

## Rules
- ALWAYS prefer graph tools over grep for code exploration
- Run `index_repository` periodically to keep graph fresh
- Use `get_graph_schema` if unsure about available node types
