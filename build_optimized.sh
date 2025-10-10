#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🚀 Starting optimized build process..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements_optimized.txt

echo "🔧 Configuring TensorFlow for memory efficiency..."
export TF_CPP_MIN_LOG_LEVEL=2
export PYTHONUNBUFFERED=1

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --clear --noinput --settings=dermai.settings_optimized

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --settings=dermai.settings_optimized

echo "🧹 Cleaning up build artifacts..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

echo "✅ Build completed successfully!"