# Ideen

> Out-of-Scope-Ideen, die während der Arbeit festgehalten werden, um sie später wieder aufzugreifen.
> Nichts hier ist verbindlich. Das ist ein Parkplatz.

## Format
- [ ] **JJJJ-MM-TT:** Ideenbeschreibung. Warum sie wichtig ist. Grobe Aufwandsschätzung.

---

## Ausstehend

- [x] **2026-06-02: workspace-mcp als öffentlichen Connector deployen.** Den read-only
      Introspektions-Server erreichbar machen, sodass ein Opus-Planungs-Chat ihn als Custom
      Connector nutzen kann (so wie brain-mcp heute erreicht wird). brain-mcps Deployment
      spiegeln: eine systemd-User-Unit, die diesen Server mit `WORKSPACE_MCP_TRANSPORT=http`
      betreibt, über Tailscale Funnel exponiert, durch eine GitHub-OAuth-App mit der `charlieLucke`-
      Allowlist abgesichert (`WORKSPACE_MCP_AUTH=github` + `WORKSPACE_GITHUB_CLIENT_ID` /
      `WORKSPACE_GITHUB_CLIENT_SECRET` / `WORKSPACE_MCP_BASE_URL`). `WORKSPACE_WORKSPACE_ROOT`
      auf den rag-workspace-Checkout zeigen lassen, sodass die Tools das echte Meta-Repo lesen.
      **Warum:** der Server ist gebaut und getestet, aber nur lokal über stdio lauffähig —
      das Deployment ist der letzte Schritt vor dem tatsächlichen Planen damit.
      **Aufwand:** klein — eine `deploy/`-Unit + eine GitHub-OAuth-App; kein neuer Code.
      **Status (2026-06-03):** ✅ Deployt & live auf **Port 443** über einen Caddy-Reverse-Proxy
      (`deploy/Caddyfile` + `deploy/caddy.service`): die eine Tailscale-Funnel → Caddy `:8088`,
      das `/` → brain-mcp und `/ws` → workspace-mcp routet (base_url `https://host/ws`).
      `:8443` wurde aufgegeben, weil Claude-Connectors Port 443 verlangen. Beide Backends extern
      durch die Funnel verifiziert (200 Discovery / 401 ohne Token), brain-mcp intakt.
      Letzte Nutzer-Schritte: den GitHub-OAuth-Callback auf `https://host/ws/auth/callback` setzen und
      den Connector `https://host/ws/mcp` in Claude hinzufügen.
