"""Spark Structured Streaming Configuration"""
import os

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
KAFKA_TOPICS = {
    'raw': 'crypto_raw',
    'clean': 'crypto_clean',
    'features': 'crypto_features',
    'predictions': 'crypto_predictions',
    'alerts': 'crypto_alerts'
}

# HDFS Configuration
HDFS_NAMENODE = os.getenv('HDFS_NAMENODE', 'hdfs://namenode:8020')
HDFS_BASE_PATH = f"{HDFS_NAMENODE}/data/crypto"
HDFS_PATHS = {
    'raw': f"{HDFS_BASE_PATH}/raw",
    'clean': f"{HDFS_BASE_PATH}/clean",
    'features': f"{HDFS_BASE_PATH}/features",
    'predictions': f"{HDFS_BASE_PATH}/predictions",
    'alerts': f"{HDFS_BASE_PATH}/alerts"
}

# Spark Streaming Configuration
SPARK_APP_NAME = "CryptoStreamingPipeline"
BATCH_INTERVAL = 30  # seconds
WATERMARK_DELAY = "0 seconds"

# Feature Engineering Windows
WINDOW_CONFIGS = {
    '1min': '1 minute',
    '5min': '5 minutes',
    '15min': '15 minutes'
}

# MLflow Configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
MLFLOW_EXPERIMENT_NAME = "crypto_streaming_experiments"

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Anomaly Detection Thresholds
ANOMALY_THRESHOLDS = {
    'z_score': 3.0,  # Standard deviations
    'volume_spike': 2.0,  # 2x normal volume
    'price_spike': 0.10  # 10% price change
}
