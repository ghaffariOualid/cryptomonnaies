"""Configuration for Kafka Producer"""
import os
from typing import List

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
KAFKA_PRODUCER_TOPIC = os.getenv('KAFKA_PRODUCER_TOPIC', 'crypto_raw')

# CoinGecko Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_COINS: List[str] = [
    'bitcoin',
    'ethereum',
    'cardano',
    'solana',
    'polkadot',
    'ripple',
    'litecoin',
    'chainlink',
    'uniswap',
    'aave'
]
COINGECKO_VS_CURRENCY = 'usd'
COINGECKO_INCLUDE_FIELDS = 'market_cap,market_cap_rank,total_volume,high_24h,low_24h,price_change_24h,price_change_percentage_24h'

# Polling Configuration
POLLING_INTERVAL = int(os.getenv('COINGECKO_API_POLLING_INTERVAL', 10))

# Producer Configuration
PRODUCER_CONFIG = {
    'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS,
    'value_serializer': lambda v: v.encode('utf-8') if isinstance(v, str) else v,
    'request_timeout_ms': 10000,
    'retries': 3
}

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
