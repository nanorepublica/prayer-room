install:
    python -m venv .venv
    pip3 install poetry
    poetry install

manage *FLAGS:
    python manage.py {{FLAGS}}

migrate:
    python manage.py migrate

tailwind:
    python manage.py tailwind build

tailwind-watch:
    python manage.py tailwind watch

bootstrap: install migrate tailwind

dev:
    python manage.py runserver 8001

worker:
    celery -A prayer_room_api worker --loglevel=info
