#!/bin/bash
set -e
# Restart Gunicorn
gunicorn --workers=4 --threads=2 --worker-class=gthread --worker-tmp-dir=/dev/shm --timeout=60 --keep-alive=5 --max-requests=1000 --max-requests-jitter=100 --backlog=2048 --bind=0.0.0.0:8000 --access-logfile=- --error-logfile=- automation.wsgi:application

echo "Application is running."