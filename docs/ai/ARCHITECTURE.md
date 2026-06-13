# Architecture

> System-level design. Update when modules, contracts, or data models change.

## Overview

workspace-mcp is a small, **read-only** MCP server that exposes a multi-repo
workspace meta-repo (its system map, routing, contracts, dependency graph and
individual repo files) to a planning chat. It is a **design-time** tool — it owns no
data, model or runtime state, and it is deliberately separate from the RAG runtime
path (titan/brain-mcp/…). Its single hard invariant is that **every tool is a pure
read**: there are no write, scaffold, or command-execution tools.

```
Planning chat (Claude/Opus)
        │  MCP (stdio  |  HTTP via Caddy /ws + GitHub OAuth)
        ▼
   workspace-mcp ──reads──▶ WORKSPACE_ROOT
                            ├── docs/ai/SYSTEM.md, ROUTING.md, CONTRACTS.md
                            ├── contracts/*            (machine-readable)
                            ├── scripts/manifest.py    (graph / names / consumers)
                            └── repos/<name>/...        (scoped, read-only file reads)
```

## Module map

```
src/workspace_mcp/
├── config.py    # Settings (env prefix WORKSPACE_): workspace_root, transport/host/port, GitHub OAuth
├── auth.py      # GitHub OAuth proxy + allowlist verifier (HTTP mode); mirrors brain-mcp/auth.py
├── server.py    # FastMCP server + the read-only tools; _read() (sandboxed) + _manifest() helpers
└── main.py      # entry point; selects stdio vs. http transport
deploy/
├── Caddyfile             # path-routing reverse proxy (/ → other MCP, /ws → this one)
├── caddy.service         # systemd user service (enabled — fronts the 443 funnel)
├── workspace-mcp.service # systemd user service (the server on :9300)
└── README.md             # connector + reverse-proxy deployment guide
```

## Tools & how they resolve

- **Doc/contract content** (`get_system_map`, `get_routing`, `get_contracts_overview`,
  `list_contracts`, `get_contract`) → read the plain-text files under
  `WORKSPACE_ROOT`, sandboxed via `is_relative_to`.
- **Manifest/graph** (`list_repos`, `dependency_graph`) → shell out to the
  workspace's own `scripts/manifest.py` (reuse the real, tested logic).
- **Scoped file read** (`read_repo_file`) → resolve `repos/<repo>/<relpath>` and
  reject anything escaping that repo's root.

Every tool returns Markdown/plain text and turns errors into a short `"Error: …"`
string — it never raises to the transport.

## External services

| Service | Connection | Purpose |
|---|---|---|
| GitHub OAuth | HTTPS (api.github.com) | authentication + login allowlist (HTTP mode only) |
| Caddy | local reverse proxy (`:8088`) | routes `/ws/*` from the shared 443 funnel to this server |
| Tailscale Funnel | public HTTPS | makes the local server reachable from the Anthropic cloud |
| workspace files | filesystem (read-only) | the meta-repo content the tools expose |

## Security & boundaries

- **Read-only is non-negotiable** — no mutating tools may ever be added; the server
  is reachable on a public path.
- **Path sandboxing** — `read_repo_file` and `get_contract` enforce strict
  `is_relative_to` checks against their authorized base dirs to block traversal.
- **Auth only in HTTP mode** — stdio is local/unauthenticated.

## Deployment

- **Local:** `stdio` transport, no auth — for development and for a local planning
  client.
- **Public connector:** the server runs on `0.0.0.0:9300` (HTTP); Caddy fronts the
  single Tailscale Funnel on port 443 and routes `/ws/*` to it, because Claude
  connectors require port 443 and that root is already used by a sibling MCP server.
  The server advertises its base URL as `https://<host>/ws`. Details:
  [`deploy/README.md`](../../deploy/README.md).
