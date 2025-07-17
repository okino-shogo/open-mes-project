#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build script for Vercel deployment"

# Install Python dependencies
pip install -r requirements.txt

# Change to the Django project directory
cd open_mes

# Change to the Django source directory
cd scr

# Collect static files for Vercel
python manage.py collectstatic --no-input --settings=base.settings_vercel

echo "Build script completed successfully"