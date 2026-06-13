# workspace_mcp

Read-only-MCP-Server, der den Workspace für Planungs-Chats bereitstellt


## Einrichtung

Erfordert [uv](https://docs.astral.sh/uv/) und Python 3.12+.

```bash
make install
```

Das installiert alle Abhängigkeiten und registriert pre-commit-Hooks.

## Entwicklung

```bash
make dev        # Dev-Server starten (im Makefile definieren)
make test       # Tests mit Coverage ausführen
make test-fast  # nur schnelle Tests ausführen
make check      # vollständiges Quality-Gate: Lint + Typen + Tests
make format     # Style-Probleme automatisch beheben
make help       # alle verfügbaren Befehle auflisten
```

## Projektstruktur

```
src/workspace_mcp/    Quellcode
tests/               Pytest-Tests (spiegelt das src/-Layout)
docs/ai/             Kontext und Pläne für KI-Agenten
.github/workflows/   CI-Konfiguration
```

## Tooling

| Tool         | Zweck                                |
|--------------|--------------------------------------|
| **uv**       | Paketmanager + Python-Installer      |
| **ruff**     | Linter + Formatter                   |
| **mypy**     | Statischer Typprüfer (Strict Mode)   |
| **pytest**   | Test-Runner mit Coverage             |
| **pre-commit** | Git-Hook-Runner                    |

Alle Tools laufen bei jedem Push in der CI.

## Arbeiten mit KI-Tools

Dieses Projekt nutzt einen strukturierten Workflow für KI-gestütztes Coding. Jeder
KI-Agent (Claude, Gemini, Cursor, Aider usw.) sollte zuerst `CLAUDE.md` lesen — sie
ist als `AGENTS.md` und `GEMINI.md` für Tool-Kompatibilität gespiegelt.

Wichtige Dateien für den KI-Kontext:

- `docs/ai/CONTEXT.md` — Stack, Konventionen, Glossar
- `docs/ai/CURRENT_TASK.md` — woran aktiv gearbeitet wird
- `docs/ai/HANDOFF.md` — Zustand für die Fortsetzung von Sitzungen über Modellwechsel hinweg
- `docs/ai/DECISIONS.md` — Protokoll der Architekturentscheidungen
- `docs/ai/plans/` — gespeicherte Pläne, erstellt von einem Planungsmodell (z. B. Opus)

Der vorgesehene Workflow:

1. Architektur- und Feature-Pläne werden von einem starken Reasoning-Modell erstellt und unter `docs/ai/plans/` gespeichert
2. Ein schnelleres/günstigeres Modell implementiert die Pläne
3. Beide referenzieren den gemeinsamen Kontext in `docs/ai/`
4. Der Zustand wird über `HANDOFF.md` über Sitzungen hinweg bewahrt

## Lizenz

Noch offen (TBD)
