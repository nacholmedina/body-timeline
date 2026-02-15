#!/bin/bash
set -e

echo "Running database migrations..."
cd api
export FLASK_APP=app:create_app
python -m flask db upgrade

echo "Building frontend..."
cd ../web
npm install
npm run build

echo "Build complete!"
