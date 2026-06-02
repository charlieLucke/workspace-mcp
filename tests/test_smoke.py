"""Smoke test for the package."""

from __future__ import annotations

from workspace_mcp.main import main


def test_main_runs() -> None:
    """Confirm main() executes without raising."""
    main()
