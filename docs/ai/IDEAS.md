# Ideas

> Out-of-scope ideas captured during work, to revisit later.
> Nothing here is committed. This is a parking lot.

## Format
- [ ] **YYYY-MM-DD:** Idea description. Why it matters. Rough effort estimate.

---

## Pending

- [x] **2026-06-02: Deploy workspace-mcp as a public connector.** Make the read-only
      introspection server reachable so an Opus planning chat can use it as a custom
      connector (the way brain-mcp is reached today). Mirror brain-mcp's deployment:
      a systemd user unit running this server with `WORKSPACE_MCP_TRANSPORT=http`,
      exposed via Tailscale Funnel, gated by a GitHub OAuth app with the `charlieLucke`
      allowlist (`WORKSPACE_MCP_AUTH=github` + `WORKSPACE_GITHUB_CLIENT_ID` /
      `WORKSPACE_GITHUB_CLIENT_SECRET` / `WORKSPACE_MCP_BASE_URL`). Point
      `WORKSPACE_WORKSPACE_ROOT` at the rag-workspace checkout so the tools read the
      real meta-repo. **Why:** the server is built and tested but only runnable locally
      over stdio — deployment is the last step before actually planning with it.
      **Effort:** small — a `deploy/` unit + a GitHub OAuth app; no new code.
      **Status (2026-06-03):** ✅ Deployed & live on **port 443** via a Caddy reverse proxy
      (`deploy/Caddyfile` + `deploy/caddy.service`): the one Tailscale Funnel → Caddy `:8088`,
      which routes `/` → brain-mcp and `/ws` → workspace-mcp (base_url `https://host/ws`).
      `:8443` was abandoned because Claude connectors require port 443. Both backends verified
      externally through the funnel (200 discovery / 401 without token), brain-mcp intact.
      Last user steps: set the GitHub OAuth callback to `https://host/ws/auth/callback` and add
      the connector `https://host/ws/mcp` in Claude.
