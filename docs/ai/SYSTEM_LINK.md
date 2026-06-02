# SYSTEM_LINK — this repo is part of a system

> Dropped into each child repo as `docs/ai/SYSTEM_LINK.md` by `./workspace.sh new` and
> kept in sync by `./workspace.sh sync-shared`. It tells an agent working *inside* this
> repo that it belongs to a larger system, and where the system brain lives.

## This repo
- **Service name:** workspace-mcp
- **Role:** <one-line responsibility>
- **Consumes:** <other services this repo calls, by contract>
- **Exposes:** <contract this repo publishes>
- **Port (local):** <port or n/a>

## Where the system brain lives
The coordinating workspace repo holds the cross-repo picture:
- System map & dependency graph → workspace `docs/ai/SYSTEM.md`
- Which repo owns what → workspace `docs/ai/ROUTING.md`
- The contracts this repo must honor → workspace `docs/ai/CONTRACTS.md` + `contracts/`
- Cross-repo decisions → workspace `docs/ai/DECISIONS.md`

## Rules that override nothing, but add one thing
Follow this repo's own `CLAUDE.md` for all local work. The one addition from being part of
a system: **a change at this repo's boundary (its exposed contract) is a workspace-level
decision** — stop and surface it rather than changing the interface here.

<!-- SHARED-AGENT-RULES:START (synced from workspace shared/agent-rules.md — do not edit here) -->
<!-- SHARED-AGENT-RULES:END -->
