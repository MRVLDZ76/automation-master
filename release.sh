#!/bin/bash
set -e

python manage.py migrate
python manage.py create_superuser

# python manage.py collectstatic --noinput

echo "Release script completed successfully."
