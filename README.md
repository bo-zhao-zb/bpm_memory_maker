# BPM Memory Maker

A Django 5.2 LTS foundation for the photo printing service described in [plan.md](plan.md).
Python 3.12 is managed by `uv`; the VM's system Python is not modified.

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```sh
uv sync --locked
uv run --env-file .env.example python manage.py migrate
uv run --env-file .env.example python manage.py runserver 127.0.0.1:8000
```

The health endpoint is at `http://127.0.0.1:8000/health/`.
When using VS Code Remote SSH, forward port 8000 in the Ports panel and open the
forwarded localhost URL. Do not expose Django's development server through the VM's
public IP or open an Azure NSG port for it.

The example environment enables development mode and SQLite. For custom settings,
use an ignored `.env` file with `uv run --env-file .env ...`, or supply environment
variables directly. Set `DATABASE_URL` to a PostgreSQL connection URL to use
PostgreSQL; CI runs against PostgreSQL 16 and SQLite.

## Checks

```sh
DJANGO_DEBUG=true uv run python manage.py test
uv run ruff check .
uv run ruff format --check .
DJANGO_DEBUG=true uv run python manage.py makemigrations --check --dry-run
```

## Deployment Boundary

Azure hosting, storage, payment, AI and fulfilment decisions remain open. This is
not yet a production deployment. Outside development, settings require an explicit
secret key and database URL and enable HTTPS redirection and secure cookies.
TLS termination, trusted proxy configuration, production process management,
static asset serving, backups, monitoring and provider credentials must be set up
before a public launch. Never commit credentials or customer photos.