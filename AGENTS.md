# Project Guidance

## Scope and Structure

- Read [README.md](README.md) for the implemented milestone and setup, and
  [plan.md](plan.md) for product intent. Planned work is not already implemented
  or an instruction to expand the current task.
- Keep the Python-first Django modular monolith: accounts, catalogue and albums
  are separate apps in one codebase. Reuse service functions for business rules.
- Uploads, background workers, AI, payments, fulfilment and Azure production
  deployment remain deferred. Do not select providers or provision resources
  without agreement.
- Use the additional guidance in [accounts/AGENTS.md](accounts/AGENTS.md),
  [albums/AGENTS.md](albums/AGENTS.md) and [templates/AGENTS.md](templates/AGENTS.md)
  when touching those areas. Keep these files concise and consistent.

## Environment and Checks

- Use Python 3.12 through `uv`, not the VM's system Python. Install reproducibly
  with `uv sync --locked`; update `pyproject.toml` and `uv.lock` together when
  deliberately changing dependencies.
- SQLite is the local default; CI is configured for PostgreSQL 16 and SQLite.
  Do not claim PostgreSQL behaviour was verified from a SQLite-only test run.
- Start with the smallest relevant Django test label, then run the full checks
  for a completed implementation milestone:

```sh
uv run --env-file .env.example python manage.py test
uv run ruff check .
uv run ruff format --check .
uv run --env-file .env.example python manage.py makemigrations --check --dry-run
```

- Generate and commit migrations for model changes. Do not rewrite previously
  committed migrations to hide schema changes.
- Bind development servers to `127.0.0.1` and use VS Code SSH port forwarding.
  Do not open Azure firewall ports or expose Django's development server.

## Working Agreements

- Inspect current files and `git status` before editing. Preserve unrelated
  user changes and keep each task focused.
- Checkpoint tested implementation milestones with local Git commits. Stage
  only intended files; do not push or deploy unless asked.
- Report review findings separately from fixes unless fixes were requested.
  Back findings with a code reference and a focused reproduction where practical.
- Never commit credentials, environment secrets, databases, customer photos or
  session tokens. Do not ask users to send secrets through chat.
- Keep secure settings outside development. The example environment is for
  local use, not a production configuration.
- Keep the frontend build-free: Django templates, local CSS/assets and small
  amounts of JavaScript only when needed. Preserve upstream asset licences.
- Update documentation and these instructions when the implemented behaviour
  or required commands change. State unverified integrations explicitly.
- Record notable behaviour and workflow changes in [CHANGELOG.md](CHANGELOG.md)
  under `Unreleased`; do not treat checkpoint commits as releases or list planned
  features as implemented.