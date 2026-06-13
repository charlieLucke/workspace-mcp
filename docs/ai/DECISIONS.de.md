# Entscheidungs-Log

> Architecture Decision Records. Nur anhängen. Ein Eintrag pro signifikanter Entscheidung.
> Das verhindert, dieselben Fragen in jeder neuen KI-Sitzung neu auszufechten.

## Format

```
## JJJJ-MM-TT: Kurztitel
**Entscheidung:** Was wir entschieden haben
**Begründung:** Warum
**Erwogene Alternativen:** Was wir verworfen haben und warum
**Konsequenzen:** Was das für die Zukunft bedeutet
```

---

## Anfangsentscheidungen (Template-Defaults)

## 2026-XX-XX: uv als Paketmanager verwenden
**Entscheidung:** uv (statt pip+venv, poetry, pdm).
**Begründung:** 10–100× schneller als pip; vereintes Werkzeug, das pip, pip-tools, virtualenv, pyenv ersetzt; Lockfile standardmäßig; getragen von Astral (dasselbe Team wie ruff).
**Erwogene Alternativen:** Poetry (langsamer, mehr Konfigurationsaufwand, getrennt vom venv-Tooling). pip+venv (kein Lockfile by default, manueller Workflow).
**Konsequenzen:** Alle Dependency-Operationen laufen über `uv add` / `uv remove` / `uv sync`. Niemals pyproject.toml-Abhängigkeiten manuell bearbeiten.

## 2026-XX-XX: ruff für Lint und Format verwenden
**Entscheidung:** ruff ersetzt black + flake8 + isort + pyupgrade.
**Begründung:** Einzelwerkzeug, deutlich schneller, konsistente Konfiguration, aktiv gepflegt.
**Konsequenzen:** black, flake8 oder isort nicht als separate Werkzeuge ergänzen.

## 2026-XX-XX: Mypy Strict Mode
**Entscheidung:** Mypy im Strict Mode ab Tag eins.
**Begründung:** Striktheit ist von Anfang an viel leichter durchzusetzen als nachzurüsten. Fängt ganze Bug-Kategorien zur Schreibzeit ab.
**Konsequenzen:** Jede Funktion braucht vollständige Type-Hints. `# type: ignore` erfordert einen Inline-Kommentar mit Begründung.
