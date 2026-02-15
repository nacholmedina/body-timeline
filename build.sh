#!/bin/bash
set -e

echo "Installing API dependencies..."
cd api
pip install -r requirements.txt

echo "Running database migrations..."
flask db upgrade

echo "Building frontend..."
cd ../web
npm install
npm run build

echo "Build complete!"
