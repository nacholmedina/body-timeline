#!/bin/bash
# Run this script to apply database migrations
set -e

cd api
export FLASK_APP=app:create_app
flask db upgrade
echo "Migrations applied successfully!"
