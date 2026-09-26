# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.10.10 AS uv

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=uv /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN DJANGO_DEBUG=false \
    DJANGO_SECRET_KEY=build-only-not-for-runtime \
    DJANGO_ALLOWED_HOSTS=localhost \
    DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    DJANGO_MEDIA_ROOT=/tmp/media \
    python manage.py collectstatic --noinput \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /srv/bpm-memory-maker/media \
    && chown -R app:app /srv/bpm-memory-maker

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/health/', headers={'X-Forwarded-Proto': 'https'}); raise SystemExit(0 if urllib.request.urlopen(request, timeout=4).status == 200 else 1)"

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=2", "--threads=2", "--timeout=60", "--access-logfile=-", "--error-logfile=-", "config.wsgi:application"]