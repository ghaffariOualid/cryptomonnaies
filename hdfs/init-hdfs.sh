#!/bin/bash
# Initialize HDFS directories for the data lake

set -e

echo "🚀 Initializing HDFS Data Lake..."

# Wait for Namenode to be ready
echo "⏳ Waiting for Namenode..."
until hadoop fs -ls / &> /dev/null; do
  echo "Waiting for Namenode to be ready..."
  sleep 2
done

echo "✅ Namenode is ready"

# Create directory structure
echo "📁 Creating HDFS directories..."

hadoop fs -mkdir -p /data/crypto/raw
hadoop fs -mkdir -p /data/crypto/clean
hadoop fs -mkdir -p /data/crypto/features
hadoop fs -mkdir -p /data/crypto/predictions
hadoop fs -mkdir -p /data/crypto/alerts

# Set permissions
hadoop fs -chmod -R 777 /data/crypto

echo "✅ HDFS Data Lake initialized successfully"
hadoop fs -ls /data/crypto/
