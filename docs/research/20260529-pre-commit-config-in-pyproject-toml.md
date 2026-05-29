# Research: Can `.pre-commit-config.yaml` settings be moved to `pyproject.toml`?

**Date**: 2026-05-29
**Project**: telegram-channel-parser

---

## Summary

The pre-commit framework itself does **not** support reading its own configuration from `pyproject.toml` — `.pre-commit-config.yaml` is required and cannot be eliminated. However, most per-tool settings (black, isort, bandit) can already live in `pyproject.toml` and be dropped from hook `args:`, while flake8 needs a third-party plugin. The current project already uses `pyproject.toml` for black and isort config, so the main remaining opportunity is cleaning up bandit's `args:` and noting flake8's limitation.

---

## Context

The project currently has:
- `.pre-commit-config.yaml` with four hooks: `autoflake` (local), `isort`, `black`, `bandit`
- `pyproject.toml` with `[tool.black]` and `[tool.isort]` sections already defined
- `flake8` listed as a dev dependency but **not present** as a pre-commit hook
- `bandit` hook passes all its arguments inline: `['-f', 'html', '-o', 'bandit-report.html', '-r', '.']`

The question is whether `.pre-commit-config.yaml` can be reduced or eliminated by moving its content to `pyproject.toml`.

---

## Findings

### 1. pre-commit framework config support in `pyproject.toml`

**Answer: No — not now, not planned.**

The pre-commit project explicitly does not support `pyproject.toml` as a config source. Multiple GitHub issues have been opened and closed without implementation:
- [Issue #1165](https://github.com/pre-commit/pre-commit/issues/1165) (2019) — original request, closed
- [Issue #2056](https://github.com/pre-commit/pre-commit/issues/2056) (2021) — follow-up, closed
- [Issue #2188](https://github.com/pre-commit/pre-commit/issues/2188) (2022) — follow-up, closed

`.pre-commit-config.yaml` is mandatory. Framework-level keys (`repos:`, `rev:`, `hooks:`, `default_language_version:`, `stages:`, `files:`, `language:`) all live there and cannot be moved.

The third-party package [`pyproject-pre-commit`](https://pypi.org/project/pyproject-pre-commit/) provides a workaround by bundling tools as project dependencies (removing the need for pinned `rev:` per-repo), but it does not eliminate the YAML file either.

---

### 2. Per-tool analysis

| Tool | Reads `pyproject.toml` natively? | Config section | Notes |
|---|---|---|---|
| **black** | Yes (only TOML supported) | `[tool.black]` | Already configured in this project. No `args:` needed in hook. |
| **isort** | Yes | `[tool.isort]` | Already configured in this project. No `args:` needed in hook. |
| **flake8** | No (not built-in) | — | Needs [`flake8-pyproject`](https://pypi.org/project/Flake8-pyproject/) plugin or `pyproject-flake8` wrapper. Not used as a hook in this project. |
| **bandit** | Partial (`bandit[toml]` extra required) | `[tool.bandit]` | Supports `exclude_dirs`, `skips`, `tests`. Output format (`-f html -o report.html`) is CLI-only and stays in `args:`. |
| **autoflake** | No | — | Local hook with no pyproject.toml support. All args stay in `.pre-commit-config.yaml`. |

**bandit detail**: Since bandit v1.7.0, a `[tool.bandit]` section is supported when bandit is installed with the `toml` extra (`bandit[toml]`). However, output-formatting flags (`-f`, `-o`) are not supported in the config file and must remain as `args:` in the hook definition. The `-r .` (recursive scan of root) is implicit when running from pre-commit and can also be dropped. Explicit `-c pyproject.toml` must be passed to the hook for bandit to read the TOML config.

---

### 3. What cannot be moved to `pyproject.toml`

The following must stay in `.pre-commit-config.yaml`:

- **Hook source coordinates**: `repo:`, `rev:` — these are pre-commit infrastructure, no TOML equivalent exists
- **Hook metadata**: `id:`, `name:`, `entry:`, `language:`, `types:`, `files:` — same
- **autoflake args**: autoflake has no pyproject.toml support at all
- **bandit output flags**: `-f html -o bandit-report.html` — CLI-only options, not supported in `[tool.bandit]`
- **Framework-level settings**: `default_language_version:`, `stages:`, `ci:` — pre-commit framework config

---

### 4. Recommended approach in 2025

The industry consensus as of 2025 is:

1. Keep `.pre-commit-config.yaml` for hook wiring (repos, revs, execution metadata)
2. Keep tool logic configuration in `pyproject.toml` (`[tool.black]`, `[tool.isort]`, `[tool.bandit]`, etc.)
3. Avoid duplicating settings in both places — if a tool reads `pyproject.toml`, remove those settings from hook `args:`
4. For flake8 specifically: prefer migrating to **ruff** (which fully supports `pyproject.toml` via `[tool.ruff]`) rather than adding `flake8-pyproject`

---

## Recommendation

For this project, the concrete actions are:

1. **No change needed for black and isort** — their `pyproject.toml` config is already authoritative; the hooks carry no `args:`, which is correct.

2. **Bandit**: The current hook args `['-f', 'html', '-o', 'bandit-report.html', '-r', '.']` are all output-formatting or path flags. None of them benefit from moving to `[tool.bandit]`. If security rule exclusions (skips/tests) were needed, those could go to `[tool.bandit]`. For now, no change is necessary unless bandit security config grows.

3. **autoflake**: Cannot be simplified; keep as-is in the local hook.

4. **flake8**: Not present as a hook. If linting is needed, prefer adding **ruff** (which replaces flake8 + isort + some bandit rules and is fully `pyproject.toml`-native) rather than adding a flake8 pre-commit hook.

5. **Do not attempt to replace `.pre-commit-config.yaml`** — it is required by the pre-commit framework and there is no supported path to eliminate it.

**Bottom line**: The project's `.pre-commit-config.yaml` is already close to minimal. The split between the two files is correct: hook wiring in YAML, tool logic in TOML.

---

## Sources

- [pre-commit: Allow pyproject.toml to define pre-commit config (Issue #1165)](https://github.com/pre-commit/pre-commit/issues/1165) — opened 2019, closed without implementation
- [pre-commit: Support pyproject.toml for configuration (Issue #2056)](https://github.com/pre-commit/pre-commit/issues/2056) — 2021
- [pre-commit: Use pyproject.toml for configuring pre-commit (Issue #2188)](https://github.com/pre-commit/pre-commit/issues/2188) — 2022
- [Black documentation: Using Black with other tools](https://black.readthedocs.io/en/stable/guides/using_black_with_other_tools.html) — confirms pyproject.toml as primary config
- [Bandit: PEP-518 support PR #401](https://github.com/PyCQA/bandit/pull/401) — adds `[tool.bandit]` support
- [Bandit: config is not in effect from pyproject.toml? (Discussion #1244)](https://github.com/PyCQA/bandit/discussions/1244) — practical limitations
- [Bandit documentation: Configuration](https://bandit.readthedocs.io/en/latest/config.html)
- [Flake8: pyproject.toml support (Issue #234)](https://github.com/PyCQA/flake8/issues/234) — not natively supported
- [flake8-pyproject on PyPI](https://pypi.org/project/Flake8-pyproject/) — third-party plugin
- [pyproject-pre-commit on PyPI](https://pypi.org/project/pyproject-pre-commit/) — community workaround package
- [Effortless Code Quality: The Ultimate Pre-Commit Hooks Guide for 2025](https://gatlenculp.medium.com/effortless-code-quality-the-ultimate-pre-commit-hooks-guide-for-2025-57ca501d9835)
