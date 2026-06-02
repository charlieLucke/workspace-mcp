"""Entry point for workspace_mcp."""

from __future__ import annotations

import logging

from workspace_mcp.config import settings
from workspace_mcp.server import mcp

log = logging.getLogger(__name__)


def main() -> None:
    """Run the MCP server."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if settings.mcp_transport == "http":
        log.info("Starting MCP server (http) on %s:%s", settings.mcp_host, settings.mcp_port)
        mcp.run(transport="http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
