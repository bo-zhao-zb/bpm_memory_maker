# BPM Memory Maker

A Django 5.2 LTS foundation for the photo printing service described in [plan.md](plan.md).
Python 3.12 is managed by `uv`; the VM's system Python is not modified.

See [CHANGELOG.md](CHANGELOG.md) for notable implemented changes and known
limitations, and [the competitor benchmark](docs/competitive-benchmark.md) for
proposed product positioning and experience goals.
The gated public-hosting pipeline and owner setup are documented in
[the Azure deployment guide](docs/deployment.md).

## Project Structure

This is a Django web application, not a distributable Python library. Its flat,
domain-oriented layout is intentional:

| Path | Responsibility |
| --- | --- |
| [config/](config/) | Django settings, root URLs and ASGI/WSGI entry points |
| [accounts/](accounts/) | Custom user model and authentication |
| [catalog/](catalog/) | Print products, admin and catalogue seeding |
| [albums/](albums/) | Album models, service-layer rules, forms, views and tests |
| [templates/](templates/) | Shared shell, reusable components and namespaced app pages |
| [static/](static/) | Local CSS, small JavaScript enhancements and licensed assets |
| [.github/workflows/](.github/workflows/) | Automated checks, including both database configurations |
| [docs/](docs/) | Design and product decisions with supporting evidence |
| [pyproject.toml](pyproject.toml) and [uv.lock](uv.lock) | Python requirements, dependency groups, lint configuration and reproducible dependencies |

Apps own their migrations and tests. Small apps currently use `tests.py`; the
larger album app uses a `tests/` package. Keep one test layout per app and split a test
module when its size warrants it. Business rules belong in service functions so
future interfaces can reuse them.

A `src/` layout is useful for packaged libraries but is not required for a modern
Django application. Separate frontend/backend repositories, a JavaScript build
pipeline and microservices are likewise not prerequisites. Retain this layout
unless an actual packaging or deployment need justifies a change.

The local `.venv`, caches and SQLite database are ignored development artefacts,
not source code or production storage. Hosting configuration will be added when
the Azure deployment approach is agreed.

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
- Responsive photo-studio interface with local photography, fonts, Lucide icons
	and a progressively enhanced password-visibility control.
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

The repository includes a production container, Compose definition, Caddy example,
VM deployment script and a disabled-by-default GitHub deployment workflow. These
files are deployment preparation, not evidence that Azure resources, DNS, backups,
alerts or a public production service have been configured or verified.

## Recovery Checkpoints

Implementation milestones are committed locally. `git log --oneline` shows recovery
points. An SSH disconnection does not discard files or commits on the VM, but local
commits do not protect against loss of the VM itself. Push to the remote repository
when ready; no deployment or cloud resource provisioning happens automatically.