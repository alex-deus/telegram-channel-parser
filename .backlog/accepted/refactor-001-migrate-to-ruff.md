# Task: Migrate Dev Toolchain to Ruff

## Metadata

- **ID**: refactor-001-migrate-to-ruff
- **Status**: accepted
- **Priority**: medium
- **Estimated Hours**: 2
- **Assigned Agent**: python-engineer
- **Dependencies**: none
- **Rejection Count**: 0 (max 3; quality-reviewer increments on reject; after 3rd rejection, task-engineer redesigns. See `${CLAUDE_PLUGIN_ROOT}/content/backlog/workflow.md` for canonical retry limits.)
- **Created By**: task-engineer
- **Created At**: 2026-05-29 06:46:37 UTC
- **Documentation**: docs/research/20260529-pre-commit-config-in-pyproject-toml.md

## Description

Replace the four separate formatting and linting tools (black, isort, autoflake, flake8) with ruff. Ruff covers all four in a single binary that is 10-100x faster and places all configuration in `[tool.ruff]` inside `pyproject.toml`, eliminating the current split between `[tool.black]` and `[tool.isort]` sections. bandit stays unchanged because ruff is not a security scanner.

## Acceptance Criteria (EARS Format)

### Functional Requirements

- [ ] WHEN `pre-commit run --all-files` is executed, the ruff-format hook runs in place of the black hook and produces no violations on the existing codebase.
- [ ] WHEN `pre-commit run --all-files` is executed, the ruff-check hook runs in place of the isort and autoflake hooks and produces no violations on the existing codebase.
- [ ] WHEN `pre-commit run --all-files` is executed, the bandit hook runs unchanged and produces the same output as before.

### Invariants / Ubiquitous

- [ ] The ruff configuration enforces line length 120 (matching the previous black and isort setting).
- [ ] The ruff configuration excludes at minimum `.git`, `tmp/`, and `data/` (matching the previous black exclusions).
- [ ] `pyproject.toml` contains no `[tool.black]` or `[tool.isort]` sections after migration.
- [ ] `pyproject.toml` dev dependencies contain no entries for black, isort, autoflake, flake8, or seed-isort-config after migration.
- [ ] `pyproject.toml` dev dependencies include ruff after migration.
- [ ] `.pre-commit-config.yaml` uses the `astral-sh/ruff-pre-commit` remote repo for ruff hooks (not a local hook).

### Unwanted Behavior

- [ ] IF a file that previously passed black formatting is encountered, THEN `ruff format --check` shall report no violations on that file.
- [ ] IF a file that previously passed isort ordering is encountered, THEN `ruff check --select I` shall report no violations on that file.

### State-Dependent Behavior

- [ ] WHILE the `[tool.poe.tasks]` section exists in `pyproject.toml`, the `isort` task shall be absent (it is obsolete without seed-isort-config).
- [ ] WHILE the `Makefile` exists, the `update-isort` target shall be absent (it is obsolete without seed-isort-config).

### Standard Gates

- [ ] All tests pass (unit, integration, e2e as applicable)
- [ ] Quality gates pass (`ruff check .` and `ruff format --check .` report zero violations)
- [ ] Documentation updated if needed
- [ ] Changes committed with proper conventional commit message

## Technical Requirements

### Implementation Details

- Replace `[tool.black]` and `[tool.isort]` sections in `pyproject.toml` with a single `[tool.ruff]` section; carry over line-length 120 and the existing exclusion paths.
- Remove black, isort, autoflake, flake8, and seed-isort-config from `[tool.poetry.group.dev.dependencies]`; add ruff.
- Replace the autoflake (local), isort, and black hooks in `.pre-commit-config.yaml` with ruff and ruff-format hooks from `astral-sh/ruff-pre-commit`; leave the bandit hook untouched.
- Remove the `isort` task from `[tool.poe.tasks]` in `pyproject.toml`.
- Remove the `update-isort` target from `Makefile`.
- Run `ruff check .` and `ruff format --check .` after configuration to confirm zero violations; fix any violations introduced by rule-set differences before committing.

### Testing Requirements

- No new test files required; the existing test suite must continue to pass after the toolchain change.
- Verify pre-commit hooks execute successfully end-to-end: `pre-commit run --all-files` exits 0.

### Performance Requirements

- No runtime performance requirements; this is a dev-toolchain-only change.

## Edge Cases to Handle

- Existing code may have import ordering or unused-import patterns that ruff flags differently from the old tools: resolve all violations before declaring the migration complete.
- `poetry.lock` must be updated after changing dev dependencies (`poetry lock` or `poetry install`).

## Out of Scope

- Changing any application source code logic.
- Adding ruff rule sets beyond the equivalents of black, isort, and autoflake (no new lint categories).
- Adding or removing bandit rules.
- CI/CD pipeline changes.
- Updating README.md or CLAUDE.md.

## Quality Review Checklist

### For Implementer (Before Marking Complete)

- [ ] All acceptance criteria checked
- [ ] Tests written and passing
- [ ] Code follows project conventions
- [ ] No debug code or print statements
- [ ] Error handling implemented
- [ ] Performance requirements met
- [ ] Structured logging added

### For Quality Reviewer (quality-reviewer agent)

- [ ] Implementation matches requirements
- [ ] Code quality standards met
- [ ] Test coverage adequate (>=80% overall, 100% critical paths)
- [ ] Security best practices followed
- [ ] Documentation accurate
- [ ] Git commit follows conventions
- [ ] Architecture compliance (service boundaries, patterns)
- [ ] Acceptance criteria use EARS keywords (WHEN, WHILE, IF/THEN, WHERE, or Ubiquitous)

## Transition Log

<!-- DO NOT EDIT MANUALLY - Agents update this section -->
<!-- Each transition MUST include: CURRENT timestamp, from_status, to_status, agent, reason -->
<!-- MANDATORY: Always get current timestamp before logging, NEVER use placeholders -->

| Date Time                    | From  | To      | Agent         | Reason/Comment        |
| ---------------------------- | ----- | ------- | ------------- | --------------------- |
| 2026-05-29 06:46:37          | draft | pending | task-engineer | Initial task creation |
| 2026-05-29 08:50:08          | pending | in-progress | python-engineer | Starting ruff migration |
| 2026-05-29 08:52:00          | in-progress | completed | python-engineer | Migration complete; zero ruff violations |
| 2026-05-29 09:05:00          | completed | accepted | quality-reviewer | All acceptance criteria met |

## Implementation Notes

- Removed black, isort, autoflake, flake8, seed-isort-config from `[tool.poetry.group.dev.dependencies]`; added `ruff = "^0.9.0"`.
- Removed `[tool.black]` and `[tool.isort]` sections from `pyproject.toml`.
- Added `[tool.ruff]` (line-length 120, excludes .git/tmp/data), `[tool.ruff.lint]` (select E, F, I), and `[tool.ruff.format]` sections.
- Removed `isort` poe task (was calling seed-isort-config, now obsolete).
- Replaced local autoflake hook + isort repo + black repo in `.pre-commit-config.yaml` with `astral-sh/ruff-pre-commit` rev v0.9.10 (ruff --fix + ruff-format hooks). Bandit hook left unchanged.
- No Makefile existed in the repo; update-isort target removal was a no-op.
- Fixed one ruff violation (E731 lambda assignment in cloner.py) and ruff auto-fixed 7 others (import ordering).
- `poetry lock` run to update lock file after dependency changes.

## Quality Review Comments

<!-- quality-reviewer agent adds review feedback here -->

### Review Round 1

- **Date**: 2026-05-29 09:05:00 UTC
- **Reviewer**: quality-reviewer
- **Decision**: accepted
- **Comments**:
  - `[tool.ruff]` present with `line-length = 120` and excludes `.git`, `tmp/`, `data/`
  - `[tool.ruff.lint]` present with `select = ["E", "F", "I"]`
  - `[tool.black]` and `[tool.isort]` sections absent from pyproject.toml
  - Dev deps: ruff present; black, isort, autoflake, flake8, seed-isort-config all absent
  - `.pre-commit-config.yaml` uses `astral-sh/ruff-pre-commit` rev v0.9.10; bandit hook unchanged; old hooks absent
  - `isort` poe task absent; only `lint` task remains
  - Makefile absent (no-op as documented)
  - poetry.lock updated: ruff present as top-level package, old tools absent

## Version Control Log

<!-- Implementer agent updates this when committing task file changes -->

| Date Time           | Git Action | Agent         | Commit Hash | Message                                          |
| ------------------- | ---------- | ------------- | ----------- | ------------------------------------------------ |
| 2026-05-29 06:46:37 | add        | task-engineer | -           | "task: create refactor-001-migrate-to-ruff"      |

## Evidence of Completion

```
$ poetry run ruff check .
All checks passed!

$ poetry run ruff format --check .
8 files already formatted
```

- 7 import-order violations auto-fixed by `ruff check --fix`
- 1 E731 (lambda assignment) manually converted to `def callback(...)` in application/utils/cloner.py
- poetry.lock regenerated with ruff 0.9.10, black/isort/autoflake/flake8/seed-isort-config removed

## References

- docs/research/20260529-pre-commit-config-in-pyproject-toml.md
