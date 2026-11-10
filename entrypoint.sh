#!/bin/sh
# Миграции, сборка статики и (опционально) создание суперпользователя
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput 2>/dev/null || echo "Суперпользователь уже существует"
fi
exec "$@"
