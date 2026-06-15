# Ideas

> Out-of-scope ideas captured during work, to revisit later.
> Nothing here is committed. This is a parking lot.

## Format
- [ ] **YYYY-MM-DD:** Idea description. Why it matters. Rough effort estimate.

---

## Pending

- [ ] **2026-06-15: `project_status` / docs-ai reader tool — answer "what's the state / what's planned next".** `read_repo_file` can already read any `docs/ai/*` file within the sandbox, so ad-hoc reads work today; what's missing is a one-call aggregator so a model (local or cloud) need not know the file layout. Add a tool that — per repo or across all — returns the current planning surface: `CURRENT_TASK.md` + `IDEAS.md` (pending only) + newest `HANDOFF.md`/`plans/*`, plus the workspace-level `docs/ai/{CURRENT_TASK,HANDOFF,PLANNING}.md`. Return structured markdown (repo → sections) so the model can summarise "status / next steps" without fuzzy search. **Why:** status/plan questions want the *authoritative current* file, not semantic top-k — a direct read beats RAG here and never goes stale. Pairs with the local-chatbot idea in brain-dashboard (its "project" mode would call this). Strictly read-only/sandboxed like the rest. *Effort: Low–Medium (one tool over the existing file-read + a small file-selection convention).*

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
