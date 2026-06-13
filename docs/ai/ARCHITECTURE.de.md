# Architektur

> Design auf Systemebene. Aktualisieren, wenn sich Module, Contracts oder Datenmodelle ändern.

## Überblick

workspace-mcp ist ein kleiner, **read-only** MCP-Server, der ein
Multi-Repo-Workspace-Meta-Repo (seine Systemkarte, Routing, Contracts,
Abhängigkeitsgraph und einzelne Repo-Dateien) einem Planungs-Chat bereitstellt. Es ist
ein **Design-Zeit**-Tool — es besitzt keine Daten, kein Modell, keinen Runtime-State
und ist bewusst vom RAG-Runtime-Pfad (titan/brain-mcp/…) getrennt. Seine eine harte
Invariante: **jedes Tool ist ein reiner Read** — es gibt keine Schreib-, Scaffold-
oder Befehlsausführungs-Tools.

```
Planungs-Chat (Claude/Opus)
        │  MCP (stdio  |  HTTP via Caddy /ws + GitHub OAuth)
        ▼
   workspace-mcp ──liest──▶ WORKSPACE_ROOT
                            ├── docs/ai/SYSTEM.md, ROUTING.md, CONTRACTS.md
                            ├── contracts/*            (maschinenlesbar)
                            ├── scripts/manifest.py    (graph / names / consumers)
                            └── repos/<name>/...        (gescopte, read-only File-Reads)
```

## Modulübersicht

```
src/workspace_mcp/
├── config.py    # Settings (Env-Präfix WORKSPACE_): workspace_root, Transport/Host/Port, GitHub-OAuth
├── auth.py      # GitHub-OAuth-Proxy + Allowlist-Verifier (HTTP-Modus); spiegelt brain-mcp/auth.py
├── server.py    # FastMCP-Server + die read-only-Tools; _read() (gesandboxt) + _manifest()-Helper
└── main.py      # Einstiegspunkt; wählt stdio- vs. http-Transport
deploy/
├── Caddyfile             # Pfad-routender Reverse-Proxy (/ → anderer MCP, /ws → dieser)
├── caddy.service         # systemd-User-Service (enabled — steht vor der 443-Funnel)
├── workspace-mcp.service # systemd-User-Service (der Server auf :9300)
└── README.md             # Connector- + Reverse-Proxy-Deployment-Anleitung
```

## Werkzeuge & wie sie auflösen

- **Doc-/Contract-Inhalte** (`get_system_map`, `get_routing`, `get_contracts_overview`,
  `list_contracts`, `get_contract`) → die Plain-Text-Dateien unter `WORKSPACE_ROOT`
  lesen, via `is_relative_to` gesandboxt.
- **Manifest/Graph** (`list_repos`, `dependency_graph`) → das eigene
  `scripts/manifest.py` des Workspaces aufrufen (die echte, getestete Logik wiederverwenden).
- **Gescopter File-Read** (`read_repo_file`) → `repos/<repo>/<relpath>` auflösen und
  alles ablehnen, was den Root dieses Repos verlässt.

Jedes Tool gibt Markdown/Plain-Text zurück und verwandelt Fehler in einen kurzen
`"Error: …"`-String — es wirft nie zum Transport.

## Externe Services

| Service | Verbindung | Zweck |
|---|---|---|
| GitHub OAuth | HTTPS (api.github.com) | Authentifizierung + Login-Allowlist (nur HTTP-Modus) |
| Caddy | lokaler Reverse-Proxy (`:8088`) | routet `/ws/*` von der geteilten 443-Funnel an diesen Server |
| Tailscale Funnel | öffentliches HTTPS | macht den lokalen Server aus der Anthropic-Cloud erreichbar |
| Workspace-Dateien | Dateisystem (read-only) | der Meta-Repo-Inhalt, den die Tools bereitstellen |

## Sicherheit & Grenzen

- **Read-only ist nicht verhandelbar** — es dürfen nie mutierende Tools ergänzt
  werden; der Server ist über einen öffentlichen Pfad erreichbar.
- **Pfad-Sandboxing** — `read_repo_file` und `get_contract` erzwingen strikte
  `is_relative_to`-Checks gegen ihre autorisierten Basis-Verzeichnisse, um Traversal zu blockieren.
- **Auth nur im HTTP-Modus** — stdio ist lokal/nicht authentifiziert.

## Deployment

- **Lokal:** `stdio`-Transport, keine Auth — für die Entwicklung und einen lokalen
  Planungs-Client.
- **Öffentlicher Connector:** der Server läuft auf `0.0.0.0:9300` (HTTP); Caddy steht
  vor der einzigen Tailscale-Funnel auf Port 443 und routet `/ws/*` an ihn, weil
  Claude-Connectors Port 443 verlangen und dieser Root bereits von einem
  Schwester-MCP-Server genutzt wird. Der Server bewirbt seine Basis-URL als
  `https://<host>/ws`. Details:
  [`deploy/README.de.md`](../../deploy/README.de.md).
