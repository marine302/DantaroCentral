#!/bin/bash
# Production deployment script

set -e

echo "🚀 Starting Dantaro Central deployment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install production dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-prod.txt

# Set production environment
export ENVIRONMENT=production

# Run database migrations (when implemented)
# alembic upgrade head

echo "✅ Deployment complete!"
echo "🌐 Starting server with Gunicorn..."

# Start the server with Gunicorn
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
