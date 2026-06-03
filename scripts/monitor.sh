#!/bin/bash
# Health check and monitoring script

echo "=== Trading Research Platform Health Check ==="
echo ""

# Check API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API: RUNNING"
else
    echo "❌ API: DOWN"
fi

# Check Dashboard
if curl -s http://localhost:8501 > /dev/null; then
    echo "✅ Dashboard: RUNNING"
else
    echo "❌ Dashboard: DOWN"
fi

# Check Docker
if docker ps | grep -q timescaledb; then
    echo "✅ PostgreSQL: RUNNING"
else
    echo "❌ PostgreSQL: DOWN"
fi

if docker ps | grep -q redis; then
    echo "✅ Redis: RUNNING"
else
    echo "❌ Redis: DOWN"
fi

echo ""
echo "=== Resource Usage ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "=== Recent Logs ==="
docker-compose logs --tail=10 2>/dev/null || echo "No logs available"
