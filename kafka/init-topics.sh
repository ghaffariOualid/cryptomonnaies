#!/bin/bash
# Kafka Topic Initialization Script

set -e

echo "🚀 Initializing Kafka Topics..."

# Wait for Kafka broker to be ready
echo "⏳ Waiting for Kafka Broker..."
until kafka-broker-api-versions.sh --bootstrap-server localhost:9092 &> /dev/null; do
  echo "Waiting for Kafka broker..."
  sleep 2
done

echo "✅ Kafka broker is ready"

# Create topics
echo "📝 Creating Kafka topics..."

topics=("crypto_raw" "crypto_clean" "crypto_features" "crypto_predictions" "crypto_alerts")

for topic in "${topics[@]}"; do
  kafka-topics.sh --create \
    --bootstrap-server localhost:9092 \
    --topic "$topic" \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists
  echo "✅ Topic '$topic' created"
done

echo "✅ All Kafka topics initialized"

# List topics
echo ""
echo "📊 Current topics:"
kafka-topics.sh --list --bootstrap-server localhost:9092
