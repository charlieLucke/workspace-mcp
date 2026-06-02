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
      **Status (2026-06-02):** ✅ Deployed & live — systemd unit `workspace-mcp` running,
      Tailscale Funnel on `:8443` → `localhost:9300`, public endpoint verified
      (200 OAuth discovery / 401 without token). Last user step: add the connector in Claude.
