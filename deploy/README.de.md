# workspace-mcp — Deployment

> Exponiert den **read-only** Workspace-Introspektions-MCP-Server als öffentlichen Claude-Custom-
> Connector, sodass ein Planungs-Chat (Opus) die Systemkarte, das Routing, die Contracts, den
> Abhängigkeitsgraphen und gescopte Repo-Dateien lesen kann, ohne Dateien von Hand einzufügen.
>
> **Lokale Nutzung braucht nichts davon:** einfach `python -m workspace_mcp` ausführen (stdio-Transport,
> kein Caddy, keine Funnel, kein OAuth). Die Schritte unten sind nur für den öffentlichen HTTP-Connector.
>
> Der Host unten ist ein **Platzhalter** — ersetze `<your-tailnet-host>.ts.net` durch
> deinen eigenen Tailscale-Funnel-Host.

## Warum ein Reverse-Proxy (die zentrale Design-Entscheidung)

Claude-Custom-Connectors funktionieren nur auf dem **Standard-Port 443** zuverlässig. brain-mcp besitzt
bereits die einzige Tailscale-Funnel des Nodes auf `:443 /`. Zwei MCP+OAuth-Server können nicht naiv
einen 443-Host teilen: die OAuth-Discovery (`/.well-known/oauth-protected-resource/...`) liegt am
Host-Root und würde kollidieren. Ein nicht-Standard-Port (`:8443`) wurde versucht und **Claude verweigerte ihn**.

Lösung: ein **Caddy-Reverse-Proxy** steht vor der einen 443-Funnel und routet nach Pfad —

```
Claude ──443──▶ Tailscale Funnel ──▶ Caddy (:8088) ──┬── /      ─▶ brain-mcp     (:9100)
                                                      └── /ws/*  ─▶ workspace-mcp (:9300)
```

workspace-mcps FastMCP-`base_url` ist auf `https://<host>/ws` gesetzt, sodass es alle seine
OAuth-/MCP-URLs unter `/ws` **bewirbt**, sie aber weiterhin an seinem eigenen Root **bedient**. Caddy mappt beworben→
bedient (siehe `Caddyfile`), unterschieden durch den `/ws`-Marker — keine Kollision mit brain-mcp.

| Sache | Wert |
|-------|-------|
| Interne Binds | brain-mcp `0.0.0.0:9100`, workspace-mcp `0.0.0.0:9300`, Caddy `:8088` (`bind 0.0.0.0`) |
| Öffentliche Basis-URL | `https://<your-tailnet-host>.ts.net/ws` |
| Connector-URL | `https://<your-tailnet-host>.ts.net/ws/mcp` |
| OAuth-Callback | `https://<your-tailnet-host>.ts.net/ws/auth/callback` |
| Runtime-Deps | keine (read-only über Workspace-Dateien; titan/Qdrant/GPU nicht erforderlich) |

> **An 0.0.0.0 binden, nie 127.0.0.1:** unter WSL2 Mirrored Networking ist ein reiner Loopback-Service
> von Windows aus unerreichbar, wo die Funnel läuft → Funnel liefert 502. Siehst du je ein
> pauschales 502 für *beide* Connectors bei intern laufenden Services, verdächtige eine **degradierte Mirrored-
> Bridge** (`ip -brief addr` zeigt nur `lo`, kein `ethN`) → Fix mit `wsl --shutdown` + Neustart.

## Services (systemd-User-Units)

- `caddy` — **enabled** (Autostart): die 443-Funnel zeigt auf ihn, er muss also immer oben sein.
- `workspace-mcp` — betreibt den Server auf `:9300` (HTTP-Transport).
- brain-mcp / brain-watcher / titan-service — die bestehenden RAG-Units (`linked`, on demand gestartet).

```bash
# Caddy (Reverse-Proxy)
systemctl --user link  ~/projects/rag-workspace/repos/workspace-mcp/deploy/caddy.service
systemctl --user enable --now caddy

# workspace-mcp-Server
systemctl --user link  ~/projects/rag-workspace/repos/workspace-mcp/deploy/workspace-mcp.service
systemctl --user daemon-reload
systemctl --user start workspace-mcp
```

## 1. Auth-Konfiguration (`.env`)

`~/projects/rag-workspace/repos/workspace-mcp/.env` (gitignored — nie committen):

```
WORKSPACE_MCP_AUTH=github
WORKSPACE_MCP_BASE_URL=https://<your-tailnet-host>.ts.net/ws
WORKSPACE_GITHUB_CLIENT_ID=Ov23li...
WORKSPACE_GITHUB_CLIENT_SECRET=...
WORKSPACE_GITHUB_ALLOWED_LOGINS=charlieLucke
```

GitHub-OAuth-App (https://github.com/settings/developers → OAuth Apps):

- **Homepage URL:** `https://<your-tailnet-host>.ts.net/ws`
- **Authorization callback URL:** `https://<your-tailnet-host>.ts.net/ws/auth/callback`

## 2. Caddy

Das einzelne Binary liegt unter `~/bin/caddy` (standalone, kein apt/sudo). Config: `deploy/Caddyfile`.
Nach Edits validieren / neu laden:

```bash
~/bin/caddy validate --config ~/projects/rag-workspace/repos/workspace-mcp/deploy/Caddyfile
systemctl --user reload caddy
```

## 3. Tailscale Funnel (Windows-Host)

Die eine 443-Funnel auf Caddy zeigen lassen (nicht direkt auf brain-mcp):

```powershell
tailscale funnel --bg http://localhost:8088
tailscale funnel status   # erwartet: https://<host>/  ->  proxy http://localhost:8088
```

Rollback auf nur-brain-mcp (falls Caddy je ein Problem ist): `tailscale funnel --bg http://localhost:9100`.

## 4. Den Connector in Claude hinzufügen

Einstellungen → Connectors → „Add custom connector":

- **URL:** `https://<your-tailnet-host>.ts.net/ws/mcp`

OAuth-Flow → GitHub-Login (erlaubtes Konto) → die acht read-only-Tools erscheinen: `list_repos`,
`get_system_map`, `get_routing`, `get_contracts_overview`, `list_contracts`, `get_contract`,
`dependency_graph`, `read_repo_file`.

## 5. Smoke-Test (durch die öffentliche Funnel)

```bash
H=https://<your-tailnet-host>.ts.net
# brain-mcp funktioniert weiterhin (Root):
curl -s -o /dev/null -w '%{http_code}\n' $H/.well-known/oauth-protected-resource/mcp     # 200
# workspace-mcp auf /ws:
curl -s -o /dev/null -w '%{http_code}\n' $H/.well-known/oauth-protected-resource/ws/mcp  # 200
curl -s -o /dev/null -w '%{http_code}\n' -X POST $H/ws/mcp                                # 401
```
