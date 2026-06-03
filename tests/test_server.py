"""Tests for the workspace-mcp toolset and sandbox constraints."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from workspace_mcp.config import settings
from workspace_mcp.server import (
    dependency_graph,
    get_contract,
    get_contracts_overview,
    get_routing,
    get_system_map,
    list_contracts,
    list_repos,
    read_repo_file,
)


@pytest.fixture()
def tmp_workspace(tmp_path: Path) -> Generator[Path, None, None]:
    """Sets up a temporary workspace directory structure that mimics the real one."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create repos.yaml
    repos_yaml = workspace / "repos.yaml"
    repos_yaml.write_text(
        """
system: test-system
services:
  - name: titan
    role: Test engine
    consumes: []
    exposes: contracts/titan.openapi.yaml
    port: 8765
  - name: brain-mcp
    role: Test brain
    consumes: [titan]
    exposes: contracts/brain-mcp.tools.json
    port: 9100
""",
        encoding="utf-8",
    )

    # Create docs/ai/
    docs_dir = workspace / "docs" / "ai"
    docs_dir.mkdir(parents=True)
    (docs_dir / "SYSTEM.md").write_text("# System Map", encoding="utf-8")
    (docs_dir / "ROUTING.md").write_text("# Routing", encoding="utf-8")
    (docs_dir / "CONTRACTS.md").write_text("# Contracts", encoding="utf-8")

    # Create contracts/
    contracts_dir = workspace / "contracts"
    contracts_dir.mkdir()
    (contracts_dir / "titan.openapi.yaml").write_text("openapi: 3.0.0", encoding="utf-8")

    # Create repos/ directories
    (workspace / "repos" / "titan" / "src" / "titan").mkdir(parents=True)
    (workspace / "repos" / "titan" / "README.md").write_text(
        "titan engine readme", encoding="utf-8"
    )
    (workspace / "repos" / "titan" / "src" / "titan" / "ingest.py").write_text(
        "print('ingest')", encoding="utf-8"
    )

    (workspace / "repos" / "brain-mcp").mkdir(parents=True)

    # Create a secret file outside the workspace root for testing traversal escape
    outside_file = tmp_path / "outside_secret.txt"
    outside_file.write_text("sensitive data", encoding="utf-8")

    # Create scripts/manifest.py fake that mimics real manifest.py behavior
    scripts_dir = workspace / "scripts"
    scripts_dir.mkdir()
    manifest_py = scripts_dir / "manifest.py"
    manifest_py.write_text(
        """
import sys

def main(argv):
    cmd = argv[0]
    if cmd == "names":
        print("titan\\nbrain-mcp")
    elif cmd == "field":
        svc, key = argv[1], argv[2]
        if svc == "titan" and key == "role":
            print("Test engine")
        elif svc == "brain-mcp" and key == "role":
            print("Test brain")
    elif cmd == "path":
        print(f"repos/{argv[1]}")
    elif cmd == "graph":
        print("brain-mcp -> titan")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
""",
        encoding="utf-8",
    )

    # Override workspace_root settings
    old_root = settings.workspace_root
    settings.workspace_root = workspace
    yield workspace
    settings.workspace_root = old_root


def test_list_repos(tmp_workspace: Path) -> None:
    """list_repos returns the formatted service names and roles."""
    res = list_repos()
    assert "- **titan**: Test engine" in res
    assert "- **brain-mcp**: Test brain" in res


def test_get_system_map(tmp_workspace: Path) -> None:
    """get_system_map returns SYSTEM.md content."""
    res = get_system_map()
    assert res == "# System Map"


def test_get_routing(tmp_workspace: Path) -> None:
    """get_routing returns ROUTING.md content."""
    res = get_routing()
    assert res == "# Routing"


def test_get_contracts_overview(tmp_workspace: Path) -> None:
    """get_contracts_overview returns CONTRACTS.md content."""
    res = get_contracts_overview()
    assert res == "# Contracts"


def test_list_contracts(tmp_workspace: Path) -> None:
    """list_contracts returns the list of files in contracts/."""
    res = list_contracts()
    assert res == "- titan.openapi.yaml"


def test_get_contract(tmp_workspace: Path) -> None:
    """get_contract returns file content for valid filename."""
    res = get_contract("titan.openapi.yaml")
    assert res == "openapi: 3.0.0"


def test_get_contract_traversal_rejection(tmp_workspace: Path) -> None:
    """get_contract rejects directory traversal attempts."""
    res = get_contract("../repos.yaml")
    assert res.startswith("Error:")
    assert "outside the contracts directory" in res


def test_dependency_graph(tmp_workspace: Path) -> None:
    """dependency_graph returns manifest.py graph command output."""
    res = dependency_graph()
    assert res == "brain-mcp -> titan"


def test_read_repo_file(tmp_workspace: Path) -> None:
    """read_repo_file reads valid files inside a repo sandbox."""
    res = read_repo_file("titan", "src/titan/ingest.py")
    assert res == "print('ingest')"


def test_read_repo_file_invalid_repo(tmp_workspace: Path) -> None:
    """read_repo_file rejects requests to unregistered repos."""
    res = read_repo_file("invalid-repo", "README.md")
    assert res.startswith("Error:")
    assert "not a registered service" in res


def test_read_repo_file_missing_file(tmp_workspace: Path) -> None:
    """read_repo_file returns error for missing files."""
    res = read_repo_file("titan", "missing.py")
    assert res.startswith("Error:")
    assert "not found" in res


def test_read_repo_file_traversal_rejection(tmp_workspace: Path) -> None:
    """read_repo_file rejects path traversal attempts."""
    # Attempt traversal out of repo base but inside workspace
    res1 = read_repo_file("titan", "../../repos.yaml")
    assert res1.startswith("Error:")
    assert "outside the repository sandbox" in res1

    # Attempt absolute escape traversal
    res2 = read_repo_file("titan", "../../../outside_secret.txt")
    assert res2.startswith("Error:")
    assert "outside the repository sandbox" in res2


def test_read_repo_file_size_cap(tmp_workspace: Path) -> None:
    """read_repo_file rejects files exceeding 200 KB size limit."""
    large_file = tmp_workspace / "repos" / "titan" / "large.txt"
    large_file.write_bytes(b"a" * (201 * 1024))  # 201 KB
    res = read_repo_file("titan", "large.txt")
    assert res.startswith("Error:")
    assert "exceeds the size limit of 200 KB" in res


def test_read_repo_file_blocks_dotenv(tmp_workspace: Path) -> None:
    """read_repo_file refuses .env (secret leak) even though it is inside the sandbox."""
    (tmp_workspace / "repos" / "titan" / ".env").write_text(
        "SECRET=should-never-be-served", encoding="utf-8"
    )
    res = read_repo_file("titan", ".env")
    assert res.startswith("Error:")
    assert "blocked" in res
    assert "should-never-be-served" not in res


def test_read_repo_file_blocks_dotdir(tmp_workspace: Path) -> None:
    """read_repo_file refuses files under a dot-directory (e.g. .git/, .venv/)."""
    gitdir = tmp_workspace / "repos" / "titan" / ".git"
    gitdir.mkdir()
    (gitdir / "config").write_text("[remote] token=secret", encoding="utf-8")
    res = read_repo_file("titan", ".git/config")
    assert res.startswith("Error:")
    assert "blocked" in res


def test_read_repo_file_blocks_disallowed_extension(tmp_workspace: Path) -> None:
    """read_repo_file refuses non-text/secret-bearing extensions (e.g. .pem)."""
    (tmp_workspace / "repos" / "titan" / "key.pem").write_text("PRIVATE KEY", encoding="utf-8")
    res = read_repo_file("titan", "key.pem")
    assert res.startswith("Error:")
    assert "not permitted" in res
