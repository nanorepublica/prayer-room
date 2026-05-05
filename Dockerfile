FROM python:3.13-slim-bookworm AS base



ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=prayer_room_api.settings \
    PORT=8000 \
    WEB_CONCURRENCY=3 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential curl \
    libpq-dev \
    postgresql-client \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system django \
    && adduser --system --ingroup django django

FROM base AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Install poetry using the image's Python 3.13 (avoiding pipx, which pulls in
# Debian Bookworm's python3.11 and confuses poetry's interpreter resolution).
RUN pip install --no-cache-dir poetry==2.0.0

COPY entrypoint README.md pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-directory

FROM base AS runtime

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /app
# Copy project code
COPY . .

# Pre-download the Tailwind CLI with curl (streams to disk in ~64KB chunks)
# rather than letting django-tailwind-cli's Python downloader buffer the whole
# ~150MB binary into memory — which OOM-kills (exit 137) on small build hosts.
# Path matches what django-tailwind-cli expects, so `tailwind build` finds it
# cached and skips its own download.
ARG TAILWIND_VERSION=3.4.13
RUN ARCH=$(uname -m) \
    && case "$ARCH" in \
         x86_64)  TW_ARCH=linux-x64 ;; \
         aarch64) TW_ARCH=linux-arm64 ;; \
         *) echo "Unsupported arch: $ARCH" >&2; exit 1 ;; \
       esac \
    && mkdir -p /root/.local/bin \
    && curl -sSL --fail \
         -o "/root/.local/bin/tailwindcss-${TW_ARCH}-${TAILWIND_VERSION}" \
         "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/tailwindcss-${TW_ARCH}" \
    && chmod +x "/root/.local/bin/tailwindcss-${TW_ARCH}-${TAILWIND_VERSION}"

# Build Tailwind CSS at image build time so collectstatic at container start
# can find prayer_room_api/static/css/tailwind.css (referenced by templates
# and required by ManifestStaticFilesStorage). DJANGO_DEBUG=false avoids
# loading debug_toolbar (a dev-only dep not installed in this image).
RUN DJANGO_DEBUG=false python manage.py tailwind build

# Run as non-root user
RUN chown -R django:django /app
USER django

# Run application
ENTRYPOINT [ "/app/entrypoint" ]
