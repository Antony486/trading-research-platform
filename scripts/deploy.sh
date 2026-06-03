#!/bin/bash
# Production deployment script

set -e

echo "🚀 Deploying Trading Research Platform..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Build and start Docker services
echo "Starting Docker services..."
docker-compose up -d --build

# Wait for database to be ready
echo "Waiting for database..."
sleep 10

# Run database migrations
echo "Running migrations..."
python3 -c "from services.api.database import init_db; import asyncio; asyncio.run(init_db())"

# Train initial model (optional)
read -p "Train initial model? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Training initial model..."
    python3 services/ml-service/training/trainer.py --symbol BTC/USDT --days 90
fi

# Start services
echo "Starting API server..."
cd services/api
nohup python3 main.py > api.log 2>&1 &
cd ../..

echo "Starting dashboard..."
nohup streamlit run services/dashboard/app.py --server.port=8501 > dashboard.log 2>&1 &

echo ""
echo "✅ Deployment complete!"
echo "Dashboard: http://localhost:8501"
echo "API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
