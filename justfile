install:
    test -d .venv || python -m venv .venv
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

# One-shot: install deps, run migrations, then start dev server
# with Tailwind in watch mode on port 8001.
dev: install migrate
    .venv/bin/python manage.py tailwind runserver 8001

# Same as `dev` but only the server (skips install/migrate)
serve:
    .venv/bin/python manage.py tailwind runserver 8001

worker:
    .venv/bin/celery -A prayer_room_api worker --loglevel=info
