#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

python manage.py createsuperuser --no-input --employee_type "PRIVILEGED" --first_name "Ahmed" --last_name "Shahir"
