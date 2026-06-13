# workspace-mcp — Deployment

> Exposes the **read-only** workspace-introspection MCP server as a public Claude custom
> connector, so a planning chat (Opus) can read the system map, routing, contracts,
> dependency graph, and scoped repo files without pasting files by hand.
>
> **Local use needs none of this:** just run `python -m workspace_mcp` (stdio transport,
> no Caddy, no Funnel, no OAuth). The steps below are only for the public HTTP connector.
>
> The host below is a **placeholder** — replace `<your-tailnet-host>.ts.net` with
> your own Tailscale Funnel host.

## Why a reverse proxy (the key design decision)

Claude custom connectors work reliably only on the **standard port 443**. brain-mcp already
owns the node's single Tailscale Funnel at `:443 /`. Two MCP+OAuth servers cannot naively share
one 443 host: the OAuth discovery (`/.well-known/oauth-protected-resource/...`) lives at the
host root and would collide. A non-standard port (`:8443`) was tried and **Claude refused it**.

Solution: a **Caddy reverse proxy** fronts the one 443 Funnel and routes by path —

```
Claude ──443──▶ Tailscale Funnel ──▶ Caddy (:8088) ──┬── /      ─▶ brain-mcp     (:9100)
                                                      └── /ws/*  ─▶ workspace-mcp (:9300)
```

workspace-mcp's FastMCP `base_url` is set to `https://<host>/ws`, so it **advertises** all its
OAuth/MCP URLs under `/ws` while still **serving** them at its own root. Caddy maps advertised→
served (see `Caddyfile`), distinguished by the `/ws` marker — no collision with brain-mcp.

| Thing | Value |
|-------|-------|
| Internal binds | brain-mcp `0.0.0.0:9100`, workspace-mcp `0.0.0.0:9300`, Caddy `:8088` (`bind 0.0.0.0`) |
| Public base URL | `https://<your-tailnet-host>.ts.net/ws` |
| Connector URL | `https://<your-tailnet-host>.ts.net/ws/mcp` |
| OAuth callback | `https://<your-tailnet-host>.ts.net/ws/auth/callback` |
| Runtime deps | none (read-only over workspace files; titan/Qdrant/GPU not required) |

> **Bind 0.0.0.0, never 127.0.0.1:** under WSL2 mirrored networking a loopback-only service is
> unreachable from Windows, where the Funnel runs → Funnel returns 502. If you ever see a
> blanket 502 for *both* connectors with services up internally, suspect a **degraded mirrored
> bridge** (`ip -brief addr` shows only `lo`, no `ethN`) → fix with `wsl --shutdown` + restart.

## Services (systemd user units)

- `caddy` — **enabled** (autostarts): the 443 Funnel points at it, so it must always be up.
- `workspace-mcp` — runs the server on `:9300` (HTTP transport).
- brain-mcp / brain-watcher / titan-service — the existing RAG units (`linked`, started on demand).

```bash
# Caddy (reverse proxy)
systemctl --user link  ~/projects/rag-workspace/repos/workspace-mcp/deploy/caddy.service
systemctl --user enable --now caddy

# workspace-mcp server
systemctl --user link  ~/projects/rag-workspace/repos/workspace-mcp/deploy/workspace-mcp.service
systemctl --user daemon-reload
systemctl --user start workspace-mcp
```

## 1. Auth configuration (`.env`)

`~/projects/rag-workspace/repos/workspace-mcp/.env` (gitignored — never commit):

```
WORKSPACE_MCP_AUTH=github
WORKSPACE_MCP_BASE_URL=https://<your-tailnet-host>.ts.net/ws
WORKSPACE_GITHUB_CLIENT_ID=Ov23li...
WORKSPACE_GITHUB_CLIENT_SECRET=...
WORKSPACE_GITHUB_ALLOWED_LOGINS=charlieLucke
```

GitHub OAuth app (https://github.com/settings/developers → OAuth Apps):

- **Homepage URL:** `https://<your-tailnet-host>.ts.net/ws`
- **Authorization callback URL:** `https://<your-tailnet-host>.ts.net/ws/auth/callback`

## 2. Caddy

The single binary lives at `~/bin/caddy` (standalone, no apt/sudo). Config: `deploy/Caddyfile`.
Validate / reload after edits:

```bash
~/bin/caddy validate --config ~/projects/rag-workspace/repos/workspace-mcp/deploy/Caddyfile
systemctl --user reload caddy
```

## 3. Tailscale Funnel (Windows host)

Point the one 443 Funnel at Caddy (not directly at brain-mcp):

```powershell
tailscale funnel --bg http://localhost:8088
tailscale funnel status   # expect: https://<host>/  ->  proxy http://localhost:8088
```

Rollback to brain-mcp-only (if Caddy is ever a problem): `tailscale funnel --bg http://localhost:9100`.

## 4. Add the connector in Claude

Settings → Connectors → "Add custom connector":

- **URL:** `https://<your-tailnet-host>.ts.net/ws/mcp`

OAuth flow → GitHub login (allowed account) → the eight read-only tools appear: `list_repos`,
`get_system_map`, `get_routing`, `get_contracts_overview`, `list_contracts`, `get_contract`,
`dependency_graph`, `read_repo_file`.

## 5. Smoke test (through the public Funnel)

```bash
H=https://<your-tailnet-host>.ts.net
# brain-mcp still works (root):
curl -s -o /dev/null -w '%{http_code}\n' $H/.well-known/oauth-protected-resource/mcp     # 200
# workspace-mcp on /ws:
curl -s -o /dev/null -w '%{http_code}\n' $H/.well-known/oauth-protected-resource/ws/mcp  # 200
curl -s -o /dev/null -w '%{http_code}\n' -X POST $H/ws/mcp                                # 401
```
