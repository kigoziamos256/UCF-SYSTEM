#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install system dependencies for WeasyPrint (PDF generation)
apt-get update
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf2.0-0

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run Django commands
python manage.py collectstatic --noinput
python manage.py migrate
