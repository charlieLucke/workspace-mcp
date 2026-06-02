# workspace-mcp — Deployment

> Exposes the **read-only** workspace-introspection MCP server as a public Claude custom
> connector, so a planning chat (Opus) can read the system map, routing, contracts,
> dependency graph, and scoped repo files without pasting files by hand.
>
> **Local use needs none of this:** just run `python -m workspace_mcp` (stdio transport,
> no Funnel, no OAuth). The steps below are only for the public HTTP connector.
>
> Mirrors `brain-mcp/deploy/`. Host below is the author's: `charliespc.taild04050.ts.net`.

## Design (decided)

| Thing | Value | Why |
|-------|-------|-----|
| Internal bind | `0.0.0.0:9300` | `127.0.0.1` is unreachable from Windows under WSL2 mirrored networking → Funnel 502 |
| Public port | **8443** | `:443` is already taken by brain-mcp (`/ → :9100`); Funnel allows 443/8443/10000 |
| Public base URL | `https://charliespc.taild04050.ts.net:8443` | clean OAuth origin, no path prefix |
| Connector URL | `https://charliespc.taild04050.ts.net:8443/mcp` | |
| OAuth callback | `https://charliespc.taild04050.ts.net:8443/auth/callback` | |
| Runtime deps | **none** | read-only over workspace files; titan/Qdrant/GPU not required |

## Prerequisites

- WSL2 with systemd (`/etc/wsl.conf` → `[boot]` `systemd=true`) and linger enabled
  (`loginctl enable-linger <user>` — already set for the RAG services).
- Tailscale on the Windows host with Funnel enabled for the node.
- A GitHub OAuth app (section 2).

---

## 1. systemd user service (WSL)

Registered as **`linked`**, not `enabled` (consistent with the RAG services — no autostart;
start on demand). It is lightweight (no GPU/VRAM), so you *may* `enable` it instead if you
want the connector always available after boot.

```bash
systemctl --user link ~/projects/rag-workspace/repos/workspace-mcp/deploy/workspace-mcp.service
systemctl --user daemon-reload
systemctl --user start workspace-mcp
systemctl --user status workspace-mcp
```

---

## 2. Auth configuration (`.env`)

Public exposure ⇒ OAuth required. Create `~/projects/rag-workspace/repos/workspace-mcp/.env`
(gitignored — never commit it):

```
WORKSPACE_MCP_AUTH=github
WORKSPACE_MCP_BASE_URL=https://charliespc.taild04050.ts.net:8443
WORKSPACE_GITHUB_CLIENT_ID=Ov23li...
WORKSPACE_GITHUB_CLIENT_SECRET=...
WORKSPACE_GITHUB_ALLOWED_LOGINS=charlieLucke
```

> Transport/host/port/workspace-root are already set by the service unit; only the OAuth
> values belong in `.env`.

Create the GitHub OAuth app (https://github.com/settings/developers → OAuth Apps → New):

- **Homepage URL:** `https://charliespc.taild04050.ts.net:8443`
- **Authorization callback URL:** `https://charliespc.taild04050.ts.net:8443/auth/callback`

Only logins in `WORKSPACE_GITHUB_ALLOWED_LOGINS` are admitted; everyone else is rejected at
the auth layer.

---

## 3. Make it publicly reachable — Tailscale Funnel

Claude connects custom connectors server-side from the Anthropic cloud, so the endpoint must
be public. On the **Windows host** — note the distinct public port `8443` (do not disturb
brain-mcp's funnel on `:443`):

```powershell
tailscale funnel --bg --https=8443 http://localhost:9300
tailscale funnel status
```

`tailscale funnel status` should now show **both**: `/ → :9100` (brain-mcp, port 443) and the
`:8443 → :9300` mapping for workspace-mcp.

**502 at the Funnel?** Usual cause: workspace-mcp bound to `127.0.0.1` instead of `0.0.0.0`
(see unit), or the service is down. Check from Windows: `iwr http://127.0.0.1:9300/mcp` must
return `401`.

---

## 4. Add the connector in Claude

Settings → Connectors → "Add custom connector":

- **URL:** `https://charliespc.taild04050.ts.net:8443/mcp`

Claude runs the OAuth flow → GitHub login (allowed account) → done. The eight read-only tools
become available: `list_repos`, `get_system_map`, `get_routing`, `get_contracts_overview`,
`list_contracts`, `get_contract`, `dependency_graph`, `read_repo_file`.

---

## 5. Smoke test

```bash
# Service running?
systemctl --user status workspace-mcp

# OAuth discovery reachable locally (expected: 200)?
curl -s -o /dev/null -w '%{http_code}\n' \
  http://127.0.0.1:9300/.well-known/oauth-protected-resource/mcp

# /mcp without a token (expected: 401)?
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  http://127.0.0.1:9300/mcp
```
