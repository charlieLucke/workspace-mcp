"""Smoke test for the package."""

from __future__ import annotations

from unittest.mock import patch

from workspace_mcp.main import main


def test_main_runs() -> None:
    """Confirm main() executes without raising."""
    with patch("workspace_mcp.main.mcp.run") as mock_run:
        main()
        mock_run.assert_called_once()
