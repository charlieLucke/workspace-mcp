"""Pydantic-Settings for workspace-mcp."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or .env."""

    workspace_root: Path = Path(__file__).resolve().parents[4]

    # MCP-Server-Transport: "stdio" (Default) or "http"
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 9300

    # OAuth Authentication for HTTP Transport
    mcp_auth: str = "none"
    mcp_base_url: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    github_allowed_logins: str = ""  # comma-separated GitHub logins

    model_config = SettingsConfigDict(env_prefix="WORKSPACE_", env_file=".env", extra="ignore")


settings = Settings()
