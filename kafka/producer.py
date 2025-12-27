"""
Kafka Producer for CoinGecko Cryptocurrency Data
Streams real-time crypto market data to Kafka topic 'crypto_raw'
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError

from config import (
    COINGECKO_API_URL,
    COINGECKO_COINS,
    COINGECKO_INCLUDE_FIELDS,
    COINGECKO_VS_CURRENCY,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_PRODUCER_TOPIC,
    LOG_LEVEL,
    POLLING_INTERVAL,
    PRODUCER_CONFIG,
)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoKafkaProducer:
    """
    Producer that fetches cryptocurrency data from CoinGecko API
    and streams it to Kafka
    """

    def __init__(self):
        """Initialize the producer with retry logic"""
        self.producer = None
        self.coins = COINGECKO_COINS
        self.polling_interval = POLLING_INTERVAL
        self.topic = KAFKA_PRODUCER_TOPIC
        self._initialize_producer()

    def _initialize_producer(self, retries: int = 10, retry_delay: int = 5) -> None:
        """
        Initialize Kafka producer with retry logic

        Args:
            retries: Number of connection attempts
            retry_delay: Seconds to wait between retries
        """
        for attempt in range(retries):
            try:
                logger.info(
                    f"Attempting to connect to Kafka: {KAFKA_BOOTSTRAP_SERVERS} "
                    f"(attempt {attempt + 1}/{retries})"
                )
                self.producer = KafkaProducer(**PRODUCER_CONFIG)
                logger.info("✅ Connected to Kafka successfully")
                return
            except Exception as e:
                logger.error(f"❌ Connection failed: {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logger.critical("Failed to connect to Kafka after multiple attempts")
                    raise

    def _fetch_coingecko_data(self) -> Optional[Dict]:
        """
        Fetch cryptocurrency data from CoinGecko API

        Returns:
            Dictionary with coin data or None if request fails
        """
        try:
            params = {
                'ids': ','.join(self.coins),
                'vs_currencies': COINGECKO_VS_CURRENCY,
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }

            logger.debug(f"Fetching data from CoinGecko API...")
            response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Successfully fetched data for {len(data)} coins")
            return data

        except requests.exceptions.Timeout:
            logger.error("CoinGecko API request timed out")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error with CoinGecko API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching CoinGecko data: {e}")
            return None

    def _parse_crypto_data(self, raw_data: Dict) -> List[Dict]:
        """
        Parse and structure CoinGecko data for Kafka

        Args:
            raw_data: Raw response from CoinGecko API

        Returns:
            List of structured messages ready for Kafka
        """
        messages = []
        timestamp = datetime.utcnow().isoformat()

        for coin_id, coin_data in raw_data.items():
            if isinstance(coin_data, dict) and 'usd' in coin_data:
                message = {
                    'id': coin_id,
                    'symbol': coin_id.upper(),
                    'price': coin_data.get('usd'),
                    'market_cap': coin_data.get('usd_market_cap'),
                    'volume': coin_data.get('usd_24h_vol'),
                    'price_change_24h': coin_data.get('usd_24h_change'),
                    'last_updated': coin_data.get('last_updated_at'),
                    'timestamp': timestamp,
                    'source': 'coingecko'
                }
                messages.append(message)
                logger.debug(f"Parsed data for {coin_id}: ${message['price']}")

        return messages

    def _send_to_kafka(self, messages: List[Dict]) -> int:
        """
        Send messages to Kafka topic

        Args:
            messages: List of messages to send

        Returns:
            Number of messages successfully sent
        """
        sent_count = 0

        for message in messages:
            try:
                message_json = json.dumps(message)
                future = self.producer.send(self.topic, value=message_json)

                # Wait for send to complete
                record_metadata = future.get(timeout=10)

                logger.info(
                    f"📤 Sent {message['symbol']}: ${message['price']} "
                    f"to {self.topic} (partition {record_metadata.partition})"
                )
                sent_count += 1

            except KafkaError as e:
                logger.error(f"Kafka error sending {message['id']}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending {message['id']}: {e}")

        return sent_count

    def start_streaming(self) -> None:
        """
        Main streaming loop: fetch data and send to Kafka
        """
        logger.info(f"🚀 Starting cryptocurrency data stream to topic '{self.topic}'")
        logger.info(f"📊 Monitoring coins: {', '.join(self.coins)}")
        logger.info(f"⏱️  Polling interval: {self.polling_interval} seconds")

        iteration = 0
        while True:
            try:
                iteration += 1
                logger.info(f"\n--- Iteration {iteration} ({datetime.utcnow().isoformat()}) ---")

                # Fetch data from CoinGecko
                raw_data = self._fetch_coingecko_data()
                if not raw_data:
                    logger.warning("No data fetched, retrying in 10s...")
                    time.sleep(10)
                    continue

                # Parse data
                messages = self._parse_crypto_data(raw_data)
                if not messages:
                    logger.warning("No messages parsed, retrying in 10s...")
                    time.sleep(10)
                    continue

                # Send to Kafka
                sent_count = self._send_to_kafka(messages)
                logger.info(f"✅ Successfully sent {sent_count}/{len(messages)} messages")

                # Wait for polling interval
                logger.debug(f"Waiting {self.polling_interval}s before next poll...")
                time.sleep(self.polling_interval)

            except KeyboardInterrupt:
                logger.info("⏹️  Stream interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in streaming loop: {e}", exc_info=True)
                time.sleep(10)

    def close(self) -> None:
        """Close the Kafka producer"""
        if self.producer:
            logger.info("Closing Kafka producer...")
            self.producer.close()
            logger.info("Producer closed")


def main():
    """Main entry point"""
    producer_instance = CryptoKafkaProducer()
    try:
        producer_instance.start_streaming()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        producer_instance.close()


if __name__ == "__main__":
    main()
