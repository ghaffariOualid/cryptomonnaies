#!/bin/bash
# Startup script for the complete platform

set -e

echo "=================================================="
echo "🚀 Crypto Streaming Platform - Startup Script"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}[1/4]${NC} Starting Docker services..."
docker-compose up -d

echo ""
echo -e "${BLUE}[2/4]${NC} Waiting for services to be healthy..."
sleep 30

# Check if services are running
services=("zookeeper" "kafka" "namenode" "datanode" "spark-master" "mlflow")
for service in "${services[@]}"; do
  if docker-compose ps $service | grep -q "Up"; then
    echo -e "${GREEN}✅${NC} $service is running"
  else
    echo "❌ $service failed to start"
    exit 1
  fi
done

echo ""
echo -e "${BLUE}[3/4]${NC} Initializing Kafka topics..."
docker-compose exec -T kafka bash -c "/app/init-topics.sh" || true

echo ""
echo -e "${BLUE}[4/4]${NC} Platform ready!"
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Crypto Streaming Platform is RUNNING${NC}"
echo "=================================================="
echo ""
echo "📊 Access Points:"
echo "  • Kafka UI:     http://localhost:8080"
echo "  • Spark UI:     http://localhost:8081"
echo "  • HDFS UI:      http://localhost:9870"
echo "  • MLflow:       http://localhost:5000"
echo ""
echo "📈 Monitor logs:"
echo "  • Producer:     docker-compose logs crypto-producer -f"
echo "  • Streaming:    docker-compose logs spark-streaming -f"
echo "  • Kafka:        docker-compose logs kafka -f"
echo ""
echo "🛑 To stop the platform:"
echo "  docker-compose down"
echo ""
