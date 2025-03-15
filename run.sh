#!/bin/bash
set -e

gunicorn automation.wsgi:application  --log-file -

echo "Application is running."