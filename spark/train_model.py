"""
Machine Learning Model Training for Cryptocurrency Prediction
Trains models for anomaly detection and trend prediction
"""

import logging
import json
from datetime import datetime
from typing import Tuple, Dict, Any

import mlflow
import mlflow.spark
import numpy as np
import pandas as pd
from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier, LogisticRegression
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, when, lit, rand
from sklearn.ensemble import IsolationForest

from spark_config import (
    HDFS_PATHS, KAFKA_BOOTSTRAP_SERVERS, LOG_LEVEL,
    MLFLOW_EXPERIMENT_NAME, MLFLOW_TRACKING_URI
)

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class CryptoMLPipeline:
    """Machine learning pipeline for cryptocurrency analysis"""

    def __init__(self):
        """Initialize ML pipeline"""
        self.spark = self._create_spark_session()
        self._setup_mlflow()

    def _create_spark_session(self) -> SparkSession:
        """Create Spark session"""
        spark = (SparkSession
                 .builder
                 .appName("CryptoMLTraining")
                 .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:8020")
                 .getOrCreate())
        logger.info("✅ Spark session created")
        return spark

    def _setup_mlflow(self) -> None:
        """Setup MLflow"""
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        logger.info("✅ MLflow configured")

    def read_features_from_hdfs(self) -> DataFrame:
        """Read engineered features from HDFS"""
        logger.info(f"Reading features from {HDFS_PATHS['features']}")
        
        df = (self.spark
              .read
              .format("parquet")
              .load(HDFS_PATHS['features']))

        logger.info(f"Loaded {df.count()} records from HDFS")
        return df

    def prepare_anomaly_detection_data(self, df: DataFrame) -> DataFrame:
        """Prepare data for anomaly detection model"""
        logger.info("Preparing data for anomaly detection...")

        prepared_df = (df
                       .select(
                           col("symbol"),
                           col("price"),
                           col("volume"),
                           col("ma_1min"),
                           col("ma_5min"),
                           col("volatility_1min"),
                           col("volume_change_pct"),
                           col("price_zscore"),
                           col("is_anomaly").cast("int").alias("label")
                       )
                       .na.drop())

        logger.info(f"Prepared {prepared_df.count()} records for training")
        return prepared_df

    def prepare_prediction_data(self, df: DataFrame) -> DataFrame:
        """Prepare data for trend prediction"""
        logger.info("Preparing data for trend prediction...")

        # Create price direction label
        prediction_df = (df
                        .withColumn("next_price", 
                                   col("price") * (1 + col("price_change_24h") / 100))
                        .withColumn("label",
                                   when(col("next_price") > col("price"), 1)
                                   .when(col("next_price") < col("price"), 0)
                                   .otherwise(lit(1)))
                        .select(
                            col("symbol"),
                            col("price"),
                            col("ma_1min"),
                            col("ma_5min"),
                            col("ma_15min"),
                            col("volatility_1min"),
                            col("volume_change_pct"),
                            col("label")
                        )
                        .na.drop())

        logger.info(f"Prepared {prediction_df.count()} records for prediction training")
        return prediction_df

    def train_anomaly_detection_model(self, train_df: DataFrame) -> Dict[str, Any]:
        """Train anomaly detection model using Random Forest"""
        logger.info("Training anomaly detection model...")

        with mlflow.start_run() as run:
            mlflow.log_param("model_type", "RandomForest_AnomalyDetection")
            mlflow.log_param("num_trees", 100)

            # Feature assembly
            feature_cols = ["price", "volume", "ma_1min", "ma_5min", "volatility_1min", "volume_change_pct"]
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")

            # Model
            rf_model = RandomForestClassifier(
                numTrees=100,
                maxDepth=10,
                minInstancesPerNode=5,
                seed=42,
                labelCol="label",
                featuresCol="features"
            )

            # Pipeline
            pipeline = Pipeline(stages=[assembler, rf_model])

            # Train/Test split
            train_data, test_data = train_df.randomSplit([0.8, 0.2], seed=42)

            # Train
            model = pipeline.fit(train_data)

            # Evaluate
            predictions = model.transform(test_data)
            evaluator = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")
            auc = evaluator.evaluate(predictions)

            logger.info(f"Anomaly Detection AUC: {auc:.4f}")
            mlflow.log_metric("auc", auc)

            # Log model
            mlflow.spark.log_model(model, "anomaly_model", registered_model_name="CryptoAnomalyDetection")

            return {
                "model": model,
                "auc": auc,
                "run_id": run.info.run_id
            }

    def train_prediction_model(self, train_df: DataFrame) -> Dict[str, Any]:
        """Train trend prediction model"""
        logger.info("Training trend prediction model...")

        with mlflow.start_run() as run:
            mlflow.log_param("model_type", "LogisticRegression_TrendPrediction")
            mlflow.log_param("max_iter", 100)

            # Feature assembly
            feature_cols = ["price", "ma_1min", "ma_5min", "ma_15min", "volatility_1min", "volume_change_pct"]
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")

            # Scaler
            scaler = StandardScaler(inputCol="features", outputCol="scaledFeatures")

            # Model
            lr_model = LogisticRegression(
                maxIter=100,
                regParam=0.01,
                labelCol="label",
                featuresCol="scaledFeatures"
            )

            # Pipeline
            pipeline = Pipeline(stages=[assembler, scaler, lr_model])

            # Train/Test split
            train_data, test_data = train_df.randomSplit([0.8, 0.2], seed=42)

            # Train
            model = pipeline.fit(train_data)

            # Evaluate
            predictions = model.transform(test_data)
            evaluator = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")
            auc = evaluator.evaluate(predictions)

            logger.info(f"Trend Prediction AUC: {auc:.4f}")
            mlflow.log_metric("auc", auc)

            # Log model
            mlflow.spark.log_model(model, "prediction_model", registered_model_name="CryptoTrendPrediction")

            return {
                "model": model,
                "auc": auc,
                "run_id": run.info.run_id
            }

    def run_training(self) -> None:
        """Execute complete training pipeline"""
        try:
            logger.info("=" * 60)
            logger.info("🤖 Starting ML Model Training")
            logger.info("=" * 60)

            # Read features
            features_df = self.read_features_from_hdfs()

            # Prepare datasets
            anomaly_data = self.prepare_anomaly_detection_data(features_df)
            prediction_data = self.prepare_prediction_data(features_df)

            # Train models
            anomaly_result = self.train_anomaly_detection_model(anomaly_data)
            prediction_result = self.train_prediction_model(prediction_data)

            logger.info("\n✅ Model training completed successfully")
            logger.info(f"Anomaly Detection Run ID: {anomaly_result['run_id']}")
            logger.info(f"Trend Prediction Run ID: {prediction_result['run_id']}")

        except Exception as e:
            logger.error(f"Training error: {e}", exc_info=True)
        finally:
            self.spark.stop()


def main():
    """Main entry point"""
    pipeline = CryptoMLPipeline()
    pipeline.run_training()


if __name__ == "__main__":
    main()
