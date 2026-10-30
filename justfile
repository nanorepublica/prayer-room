port := "8004"

# uv's Python 3.13 (matches the Dockerfile); poetry then installs into it.
install:
    test -d .venv || uv venv --seed --python 3.13 .venv
    .venv/bin/pip install --quiet poetry
    .venv/bin/poetry install

manage *FLAGS:
    .venv/bin/python manage.py {{FLAGS}}

migrate:
    .venv/bin/python manage.py migrate

tailwind:
    .venv/bin/python manage.py tailwind build

tailwind-watch:
    .venv/bin/python manage.py tailwind watch

# Install, migrate, then run the server with Tailwind watching in the background; `just logs` follows it, `just stop` ends it.
dev: install migrate
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f .dev.pid ] && kill -0 "$(cat .dev.pid)" 2>/dev/null; then
        echo "already running (pid $(cat .dev.pid))"; exit 0
    fi
    set -m  # own process group, so stop also ends the Tailwind watcher
    nohup .venv/bin/python manage.py tailwind runserver {{ port }} > .dev.log 2>&1 &
    echo $! > .dev.pid
    sleep 3
    kill -0 "$(cat .dev.pid)" 2>/dev/null || { cat .dev.log; rm -f .dev.pid; exit 1; }
    echo "prayer-room on http://localhost:{{ port }} (pid $(cat .dev.pid)); just logs to follow"

stop:
    #!/usr/bin/env bash
    [ -f .dev.pid ] || { echo "not running"; exit 0; }
    kill -- -"$(cat .dev.pid)" 2>/dev/null || true
    rm -f .dev.pid

logs:
    tail -f .dev.log

# The dev database is db.sqlite3; migrate is all it needs.
seed: migrate

# Same as `dev` but in the foreground, skipping install/migrate.
serve:
    .venv/bin/python manage.py tailwind runserver {{ port }}

tw-dev:
    python manage.py tailwind watch

tw-build:
    python manage.py tailwind build
