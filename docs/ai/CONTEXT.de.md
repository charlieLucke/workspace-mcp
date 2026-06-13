# Projektkontext

> Zuerst lesen. Unter 200 Zeilen halten. Mit der Weiterentwicklung des Projekts aktualisieren.

## Was dieses Projekt macht

`workspace-mcp` ist ein read-only Model-Context-Protocol-(MCP-)Server, der strukturelle Metadaten und Inhalte des Workspace-Meta-Repos (Systemkarten, Routing, Contracts, Abhängigkeitsgraphen und gescopte File-Reads) für Planungs-Chats bereitstellt.

## Stack
- **Sprache:** Python 3.12+
- **Kern-Bibliothek:** FastMCP (MCP-Server)
- **Settings:** Pydantic-Settings (Präfix: `WORKSPACE_`)
- **Paketmanager:** uv
- **Test-Runner:** pytest
- **Lint/Format:** ruff
- **Typprüfer:** mypy (strict)
- **CI:** GitHub Actions
- **Pre-commit:** aktiviert

## Security-Invarianten
- **Read-Only-Regel:** Der Server darf unter keinen Umständen mutierende, schreibende, befehlsausführende oder Shell-/Code-ausführende Tools definieren. Jedes Tool ist strikt ein Read.
- **Path-Traversal-Sandboxing:** File-Read-Pfade müssen strikt mit `is_relative_to` gegen die autorisierten Basis-Verzeichnisse geprüft werden (z. B. Repository-Roots oder den Contracts-Ordner), um Directory-Traversal-Escapes zu verhindern.

## Projektaufbau
```
src/workspace_mcp/    # hier liegt der gesamte Quellcode
tests/               # spiegelt das src/-Layout
docs/ai/             # Doku für KI-Agenten
.github/workflows/   # CI
```

## Konventionen

### Code-Stil
- Zeilenlänge: 100
- Anführungszeichen: doppelt
- Type-Hints auf allen Funktionssignaturen erforderlich (mypy strict)
- Docstrings: Google-Stil für öffentliche APIs
- `from __future__ import annotations` am Anfang jedes Moduls

### Fehlerbehandlung
- Spezifische Exceptions werfen, kein nacktes `Exception`
- Eigene Exceptions erben von einer projektspezifischen Basisklasse
- Keine nackten `except:`-Klauseln
- Exceptions nicht abfangen, nur um sie zu verschlucken

### Benennung
- Module: `lower_snake_case`
- Klassen: `PascalCase`
- Funktionen/Variablen: `lower_snake_case`
- Konstanten: `UPPER_SNAKE_CASE`
- Privat: führender Unterstrich

### Testing
- Eine Testdatei pro Quellmodul: `src/foo/bar.py` → `tests/foo/test_bar.py`
- pytest-Fixtures verwenden, nicht `setUp`/`tearDown`
- Langsame Tests mit `@pytest.mark.slow` markieren
- Integrationstests mit `@pytest.mark.integration` markieren

### Commits
- Format: `<type>: <subject>` (Typen: feat, fix, refactor, test, docs, chore)
- Imperativ: „add X" nicht „added X"
- Eine logische Änderung pro Commit

## Befehle (immer diese verwenden)
- `make install` — Abhängigkeiten und pre-commit-Hooks installieren
- `make test` — Tests mit Coverage ausführen
- `make check` — vollständiges Quality-Gate (Lint + Typen + Tests)
- `make format` — Stil automatisch korrigieren

## Bekannte Fallstricke
*(Entdeckungen hier anhängen, sobald du sie lernst. Beispiele: API-Rate-Limits, Bibliotheks-Eigenheiten, umgebungsspezifische Bugs.)*

## Glossar
*(Domänenspezifische Begriffe, die in diesem Projekt verwendet werden. Hilft KI-Agenten, die Fachsprache zu verstehen.)*
