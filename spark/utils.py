"""
Spark DataFrame, Kafka and HDFS utilities
"""

import logging
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, from_json, schema_of_json

logger = logging.getLogger(__name__)


def create_kafka_source(spark, bootstrap_servers: str, topic: str, schema_df=None) -> DataFrame:
    """Create Kafka stream source"""
    return (spark
            .readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", bootstrap_servers)
            .option("subscribe", topic)
            .option("startingOffsets", "latest")
            .load())


def write_to_parquet(df: DataFrame, path: str, checkpoint_id: str) -> None:
    """Write streaming DataFrame to Parquet on HDFS"""
    query = (df
             .writeStream
             .format("parquet")
             .mode("append")
             .option("path", path)
             .option("checkpointLocation", f"/tmp/checkpoint_{checkpoint_id}")
             .partitionBy("symbol")
             .start())
    return query


def write_to_kafka(df: DataFrame, bootstrap_servers: str, topic: str) -> None:
    """Write DataFrame to Kafka topic"""
    query = (df
             .writeStream
             .format("kafka")
             .option("kafka.bootstrap.servers", bootstrap_servers)
             .option("topic", topic)
             .option("checkpointLocation", f"/tmp/checkpoint_kafka_{topic}")
             .start())
    return query
