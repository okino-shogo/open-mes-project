#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Change to the Django project directory
cd scr

# Collect static files
python manage.py collectstatic --no-input --settings=base.settings_render

# Apply database migrations
python manage.py migrate --settings=base.settings_render

# Create superuser if it doesn't exist
python manage.py shell --settings=base.settings_render <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Admin user created')
else:
    print('Admin user already exists')
EOF