# Steam Price Tracker - Agents

## Project Overview

Price monitoring platform for Steam Marketplace items (CS2, TBH). Periodic collection with historical storage.

## Agent Reading Order

1. **This file** (AGENTS.md)
2. `.ai-context/project/vision.md` - Project goals
3. `.ai-context/decisions/` - Key decisions
4. Relevant architecture docs

## How to Operate

1. Read task context from `.ai-context/sessions/current-task.md`
2. Check relevant domain/architecture docs
3. Implement with type hints and error handling
4. Update documentation if needed
5. Log all significant changes

## Global Rules

### Always
- Use type hints on all functions
- Add docstrings to public APIs
- Handle Steam API errors gracefully
- Respect rate limits (3s delay, 20 req/min max)
- Log errors with context
- Keep modules small and focused

### Never
- Make real-time requests to Steam for users
- Commit secrets or .env files
- Manipulate game memory or processes
- Use synchronous blocking in async code
- Make massive parallel requests
- Use `cd /d` or any directory change in shell commands — use `workdir` parameter instead
- Assume the working directory is anything other than the project root

## Architecture

```
AGENTS.md (this file) ← Entry point
        ↓
.ai-context/
├── project/       # Vision, roadmap, glossary
├── architecture/ # Backend, frontend, database, infra
├── domain/        # Business rules, pricing, entities
├── engineering/   # Coding standards, testing, security
├── agents/        # Agent profiles
├── decisions/      # Architectural decisions
└── sessions/      # Current task state
```

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `app/api/routes.py` | REST API endpoints |
| `app/collectors/steam.py` | Steam API collector |
| `app/scheduler/tasks.py` | Collection jobs |

## Decision Process

For architectural decisions:
1. Document in `.ai-context/decisions/`
2. Follow ADR format (Context, Problem, Decision, Consequences)
3. Number sequentially: 001, 002, etc.