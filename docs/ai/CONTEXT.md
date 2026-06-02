# Project Context

> Read this first. Keep under 200 lines. Update as the project evolves.

## What this project does

`workspace-mcp` is a read-only Model Context Protocol (MCP) server that exposes structural metadata and content of the workspace meta-repo (system maps, routing, contracts, dependency graphs, and scoped file reads) to planning chats.

## Stack
- **Language:** Python 3.12+
- **Core Library:** FastMCP (MCP server)
- **Settings:** Pydantic-Settings (prefix: `WORKSPACE_`)
- **Package manager:** uv
- **Test runner:** pytest
- **Lint/format:** ruff
- **Type checker:** mypy (strict)
- **CI:** GitHub Actions
- **Pre-commit:** enabled

## Security Invariants
- **Read-Only Rule:** The server must under no circumstances define mutating, writing, command execution, or shell/code execution tools. Every tool is strictly a read.
- **Path Traversal Sandboxing:** File read paths must be strictly checked using `is_relative_to` against the authorized base directories (e.g., repository roots or the contracts folder) to prevent directory traversal escapes.

## Project Layout
```
src/workspace_mcp/    # all source code lives here
tests/               # mirrors src/ layout
docs/ai/             # AI agent docs
.github/workflows/   # CI
```

## Conventions

### Code style
- Line length: 100
- Quotes: double
- Type hints required on all function signatures (mypy strict)
- Docstrings: Google style for public APIs
- `from __future__ import annotations` at top of every module

### Error handling
- Raise specific exceptions, not bare `Exception`
- Custom exceptions inherit from a project-specific base class
- No bare `except:` clauses
- Don't catch exceptions just to silence them

### Naming
- Modules: `lower_snake_case`
- Classes: `PascalCase`
- Functions/variables: `lower_snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: leading underscore

### Testing
- One test file per source module: `src/foo/bar.py` → `tests/foo/test_bar.py`
- Use pytest fixtures, not `setUp`/`tearDown`
- Mark slow tests with `@pytest.mark.slow`
- Mark integration tests with `@pytest.mark.integration`

### Commits
- Format: `<type>: <subject>` (types: feat, fix, refactor, test, docs, chore)
- Imperative mood: "add X" not "added X"
- One logical change per commit

## Commands (always use these)
- `make install` — install deps and pre-commit hooks
- `make test` — run tests with coverage
- `make check` — full quality gate (lint + types + tests)
- `make format` — auto-fix style

## Known pitfalls
*(Append discoveries here as you learn them. Examples: API rate limits, library quirks, env-specific bugs.)*

## Glossary
*(Domain-specific terms used in this project. Helps AI agents understand business language.)*
