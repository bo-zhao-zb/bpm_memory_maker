# BPM Memory Maker

A Django 5.2 LTS foundation for the photo printing service described in [plan.md](plan.md).
Python 3.12 is managed by `uv`; the VM's system Python is not modified.

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```sh
uv sync --locked
uv run --env-file .env.example python manage.py migrate
uv run --env-file .env.example python manage.py seed_catalog
uv run --env-file .env.example python manage.py createsuperuser
uv run --env-file .env.example python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/` and sign in with the development account created by
`createsuperuser`. Enter your password directly in the terminal when prompted.
The health endpoint at `/health/` is a liveness check only, not a database or
worker readiness check.
When using VS Code Remote SSH, forward port 8000 in the Ports panel and open the
forwarded localhost URL. Do not expose Django's development server through the VM's
public IP or open an Azure NSG port for it.

The example environment enables development mode and SQLite. For custom settings,
use an ignored `.env` file with `uv run --env-file .env ...`, or supply environment
variables directly. Set `DATABASE_URL` to a PostgreSQL connection URL to use
PostgreSQL; CI runs against PostgreSQL 16 and SQLite.

## Implemented Milestone

- Custom user model and Django admin.
- Private album list, creation, viewing, renaming, size selection and confirmed deletion.
- Version checks reject stale edits and deletes; non-draft and expired albums are read-only.
- Configurable draft retention and per-album photo limits.
- Administrator-managed print sizes. `seed_catalog` adds the four planned sizes
	without replacing administrator changes; these are not fulfilment-provider products.
- Responsive Django templates with locally served fonts and Lucide icons.
- Google/Facebook OAuth entry points through django-allauth; no automatic account
	linking by matching email. Live provider callbacks still require credentials and testing.

Only album metadata is stored in this milestone. Uploads, photo limits during upload,
expiry notifications/deletion jobs, AI, checkout and fulfilment are not implemented.
Album admin is read-only; workflow actions must not bypass the service's concurrency
checks. Print products can be edited or deactivated; referenced products cannot be deleted.

## Authentication

Password sign-in on the application login page is available only with
`DJANGO_DEBUG=true` for development. There is no public password registration.
Google and Facebook buttons appear only when both client ID and client secret are
configured for that provider. Use an ignored environment file or server-side secrets;
never enter secrets into chat or commit them.

Set `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` and/or
`FACEBOOK_CLIENT_ID` / `FACEBOOK_CLIENT_SECRET`. Register exact callback URLs with
the providers, for example:

```text
http://localhost:8000/accounts/google/login/callback/
http://localhost:8000/accounts/facebook/login/callback/
```

Use HTTPS and the final public domain for production. Provider-specific restrictions
may require an HTTPS development hostname; configure `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS` accordingly. Consent-screen setup, Facebook app review,
verified domains and real callback testing are external launch requirements.
Do not duplicate provider credentials in Django admin and environment settings.
Development email uses an in-memory backend and sends no email.

## Checks

```sh
DJANGO_DEBUG=true uv run python manage.py test
uv run ruff check .
uv run ruff format --check .
DJANGO_DEBUG=true uv run python manage.py makemigrations --check --dry-run
```

The tests cover ownership, CSRF, stale edits, immutable states, expiry checks,
catalogue validation, sign-in/out, OAuth initiation and the complete album workflow.
Live OAuth callbacks and PostgreSQL-specific behaviour are separate integration checks.

## Deployment Boundary

Azure hosting, storage, payment, AI and fulfilment decisions remain open. This is
not yet a production deployment. Outside development, settings require an explicit
secret key and database URL and enable HTTPS redirection and secure cookies.
TLS termination, trusted proxy configuration, production process management,
static asset serving, backups, monitoring and provider credentials must be set up
before a public launch. Django admin still uses password authentication and needs
separate MFA/access restrictions before production. Account erasure, support audit
workflows and real retention enforcement are also pending. Never commit credentials
or customer photos. Dependency versions are recorded in `uv.lock`; review security
updates regularly.

## Recovery Checkpoints

Implementation milestones are committed locally. `git log --oneline` shows recovery
points. An SSH disconnection does not discard files or commits on the VM, but local
commits do not protect against loss of the VM itself. Push to the remote repository
when ready; no deployment or cloud resource provisioning happens automatically.