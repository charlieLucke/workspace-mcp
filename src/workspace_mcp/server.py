"""FastMCP server — exposes workspace repository metadata and content as read-only tools."""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import TYPE_CHECKING

from fastmcp import FastMCP

from workspace_mcp.auth import build_github_auth
from workspace_mcp.config import settings

if TYPE_CHECKING:
    from fastmcp.server.auth.oauth_proxy import OAuthProxy

log = logging.getLogger(__name__)


def _build_auth() -> OAuthProxy | None:
    """Build the OAuth provider when HTTP auth is enabled, else None.

    Auth applies only to the HTTP transport; stdio is local and unauthenticated.
    Raises if WORKSPACE_MCP_AUTH=github but required settings are missing.
    """
    if settings.mcp_transport != "http" or settings.mcp_auth != "github":
        return None
    allowed_logins = {
        login.strip().lower()
        for login in settings.github_allowed_logins.split(",")
        if login.strip()
    }
    missing = [
        name
        for name, value in (
            ("WORKSPACE_MCP_BASE_URL", settings.mcp_base_url),
            ("WORKSPACE_GITHUB_CLIENT_ID", settings.github_client_id),
            ("WORKSPACE_GITHUB_CLIENT_SECRET", settings.github_client_secret),
            ("WORKSPACE_GITHUB_ALLOWED_LOGINS", settings.github_allowed_logins),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "WORKSPACE_MCP_AUTH=github requires these settings: " + ", ".join(missing)
        )
    log.info("OAuth enabled (GitHub), allowlist: %s", sorted(allowed_logins))
    return build_github_auth(
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret,
        base_url=settings.mcp_base_url,
        allowed_logins=allowed_logins,
    )


# Read-only FastMCP server initialization
mcp: FastMCP = FastMCP("workspace", auth=_build_auth())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read(rel: str) -> str:
    """Read a file under settings.workspace_root, sandboxed via is_relative_to."""
    try:
        base = settings.workspace_root.resolve()
        target = (base / rel).resolve()
        if not target.is_relative_to(base):
            return f"Error: Path {rel!r} is outside the workspace root."
        if not target.is_file():
            return f"Error: File {rel!r} not found."
        return target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading {rel!r}: {e}"


def _manifest(*args: str) -> str:
    """Shell out to the workspace's own scripts/manifest.py using sys.executable."""
    manifest_path = settings.workspace_root / "scripts" / "manifest.py"
    res = subprocess.run(
        [sys.executable, str(manifest_path), *args],
        cwd=settings.workspace_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout


# Files read_repo_file is allowed to return: source, docs, config — never secrets.
# The sandbox stops escaping a repo; this allowlist stops reading secrets *inside* it.
_ALLOWED_SUFFIXES: frozenset[str] = frozenset(
    {
        ".py", ".pyi", ".md", ".rst", ".txt", ".toml", ".yaml", ".yml", ".json",
        ".ini", ".cfg", ".conf", ".sh", ".bash", ".sql", ".js", ".ts", ".tsx",
        ".jsx", ".html", ".css", ".lock",
    }
)
_ALLOWED_NAMES: frozenset[str] = frozenset(
    {"Makefile", "Dockerfile", "README", "LICENSE", "CHANGELOG"}
)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_repos() -> str:
    """List all service repositories in the workspace with their roles.

    Returns:
        Markdown list of services and their roles.
    """
    try:
        names_out = _manifest("names").strip()
        if not names_out:
            return "_No services found in manifest._"
        repos = []
        for name in names_out.splitlines():
            name = name.strip()
            if not name:
                continue
            role = _manifest("field", name, "role").strip()
            repos.append(f"- **{name}**: {role}")
        return "\n".join(repos)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_system_map() -> str:
    """Get the contents of the system architecture map (docs/ai/SYSTEM.md).

    Returns:
        The markdown content of the system map.
    """
    return _read("docs/ai/SYSTEM.md")


@mcp.tool()
def get_routing() -> str:
    """Get the behavior routing guidelines (docs/ai/ROUTING.md).

    Returns:
        The markdown content of the routing guidelines.
    """
    return _read("docs/ai/ROUTING.md")


@mcp.tool()
def get_contracts_overview() -> str:
    """Get the contract registry overview (docs/ai/CONTRACTS.md).

    Returns:
        The markdown content of the contract overview.
    """
    return _read("docs/ai/CONTRACTS.md")


@mcp.tool()
def list_contracts() -> str:
    """List all machine-readable contract filenames in the contracts/ directory.

    Returns:
        Markdown list of contract files.
    """
    try:
        contracts_dir = settings.workspace_root / "contracts"
        # Validate sandbox checks: contracts_dir must be under workspace_root
        if not contracts_dir.resolve().is_relative_to(settings.workspace_root.resolve()):
            return "Error: contracts directory is outside workspace root."
        if not contracts_dir.is_dir():
            return "_No contracts directory found._"
        files = sorted([f.name for f in contracts_dir.iterdir() if f.is_file()])
        if not files:
            return "_No contract files found._"
        return "\n".join(f"- {f}" for f in files)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_contract(name: str) -> str:
    """Get the contents of a specific contract file from the contracts/ directory.

    Args:
        name: Filename of the contract (e.g. "titan.openapi.yaml").

    Returns:
        The contents of the contract file.
    """
    try:
        base = (settings.workspace_root / "contracts").resolve()
        target = (base / name).resolve()
        if not target.is_relative_to(base):
            return f"Error: Path {name!r} is outside the contracts directory."
        if not target.is_file():
            return f"Error: Contract {name!r} not found."
        return target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def dependency_graph() -> str:
    """Get the dependency graph output (consumer -> provider edges).

    Returns:
        A text representation of the dependency graph.
    """
    try:
        return _manifest("graph").strip()
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def read_repo_file(repo: str, relpath: str) -> str:
    """Read the contents of a specific file inside a repository, sandboxed to that repo.

    Args:
        repo: The name of the service repository (e.g. "titan", "brain-mcp").
        relpath: Relative path to the file within the repository (e.g. "src/titan/ingest.py").

    Returns:
        The file contents as a string.
    """
    try:
        # Validate that the repo is one of the manifest's service names
        names_out = _manifest("names").strip().splitlines()
        valid_repos = {n.strip() for n in names_out if n.strip()}
        if repo not in valid_repos:
            return f"Error: Repository {repo!r} is not a registered service."

        # Find the path of the repo using manifest.py
        repo_path_str = _manifest("path", repo).strip()
        base = (settings.workspace_root / repo_path_str).resolve()
        target = (base / relpath).resolve()

        if not target.is_relative_to(base):
            return f"Error: Path {relpath!r} is outside the repository sandbox ({repo})."

        # Security: never serve secret-bearing or non-text files. Block dotfiles/dot-dirs
        # anywhere in the requested path (.env, .git, .venv, .ssh, ...) and restrict to a
        # known source/docs/config allowlist.
        rel_parts = target.relative_to(base).parts
        if any(part.startswith(".") for part in rel_parts):
            return f"Error: {relpath!r} is blocked (dotfiles/secret files are not readable)."
        if target.name not in _ALLOWED_NAMES and target.suffix.lower() not in _ALLOWED_SUFFIXES:
            return (
                f"Error: file type of {relpath!r} is not permitted "
                "(only source, docs and config — never secrets)."
            )

        if not target.is_file():
            return f"Error: File {relpath!r} not found in repository {repo}."

        # Sane size cap check: e.g. 200 KB
        if target.stat().st_size > 200 * 1024:
            return f"Error: File {relpath!r} exceeds the size limit of 200 KB."

        return target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error: {e}"
