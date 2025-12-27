# 🚀 Quick Reference Card

## Commands Cheatsheet

### Starting & Stopping

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View running services
docker-compose ps

# View service logs
docker-compose logs [service-name] -f

# Restart a service
docker-compose restart [service-name]
```

---

## Web Interfaces

| Service | URL | Purpose |
|---------|-----|---------|
| Kafka UI | http://localhost:8080 | Topic/message monitoring |
| Spark Master | http://localhost:8081 | Cluster dashboard |
| HDFS Namenode | http://localhost:9870 | File browser |
| MLflow | http://localhost:5000 | Model tracking |

---

## Common Kafka Operations

```bash
# List topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Read messages from topic
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto_raw \
  --from-beginning \
  --max-messages 5

# Create topic
docker-compose exec kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic my-topic \
  --partitions 3 \
  --replication-factor 1

# Delete topic
docker-compose exec kafka kafka-topics --delete \
  --bootstrap-server localhost:9092 \
  --topic my-topic
```

---

## Common HDFS Operations

```bash
# List files
docker-compose exec namenode hadoop fs -ls /data/crypto/

# View file content
docker-compose exec namenode hadoop fs -cat /data/crypto/clean/symbol=bitcoin/*.parquet

# Get file count
docker-compose exec namenode hadoop fs -count /data/crypto/

# Delete directory
docker-compose exec namenode hadoop fs -rm -r /data/crypto/temp/

# Create directory
docker-compose exec namenode hadoop fs -mkdir /data/crypto/custom/
```

---

## Spark Operations

```bash
# Submit streaming job
docker-compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /app/spark/streaming_job.py

# Submit training job
docker-compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /app/spark/train_model.py

# Check Spark UI
# http://localhost:8081

# Submit interactive shell
docker-compose exec spark-master pyspark \
  --master spark://spark-master:7077
```

---

## Monitoring & Debugging

```bash
# Health check
python3 health_check.py

# Producer logs (real-time)
docker-compose logs crypto-producer -f

# Streaming logs (real-time)
docker-compose logs spark-streaming -f

# Kafka logs
docker-compose logs kafka -f | grep -i error

# HDFS logs
docker-compose logs namenode -f
```

---

## Data Inspection

```bash
# Check producer is sending data
docker-compose logs crypto-producer | grep "📤" | tail -10

# Read latest alerts
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto_alerts \
  --from-beginning \
  --timeout-ms 5000

# Check HDFS storage usage
docker-compose exec namenode hadoop fs -du -h /data/crypto/

# List files in clean layer
docker-compose exec namenode hadoop fs -find /data/crypto/clean/ -type f
```

---

## ML Model Operations

```bash
# View training logs
docker-compose logs spark-streaming | grep -i "training\|auc\|model"

# List registered models (via MLflow API)
curl http://localhost:5000/api/2.0/mlflow/registered-models/list | python -m json.tool

# View experiment runs
curl http://localhost:5000/api/2.0/mlflow/experiments/list | python -m json.tool

# Get model version
curl http://localhost:5000/api/2.0/mlflow/model-versions/list?name=CryptoAnomalyDetection
```

---

## Performance Tuning

```bash
# Increase Spark executor memory
# Edit docker-compose.yml:
# SPARK_EXECUTOR_MEMORY: 4g

# Increase Kafka partitions
docker-compose exec kafka kafka-topics --alter \
  --bootstrap-server localhost:9092 \
  --topic crypto_raw \
  --partitions 6

# Increase Spark workers
# Add new service in docker-compose.yml and restart
docker-compose up -d spark-worker-2
```

---

## Cleaning & Reset

```bash
# Clean up stopped containers
docker-compose down

# Remove all data (CAUTION!)
docker-compose down -v

# Clean Docker system
docker system prune -a

# Remove specific service data
docker volume rm crypto_namenode
```

---

## Troubleshooting Quick Fixes

| Issue | Command |
|-------|---------|
| Port already in use | `lsof -i :9092` or `netstat -ano \| findstr :9092` |
| HDFS permission error | `docker-compose exec namenode hadoop fs -chmod -R 777 /data/` |
| Kafka broker offline | `docker-compose restart kafka` |
| Spark job stuck | Check logs, restart `spark-streaming` |
| MLflow not responding | `docker-compose restart mlflow` |
| High memory usage | Reduce `SPARK_EXECUTOR_MEMORY` in docker-compose.yml |

---

## Configuration Quick Links

- **Kafka**: `kafka/config.py`
- **Spark**: `spark/spark_config.py`
- **Docker**: `docker-compose.yml`
- **Requirements**: `requirements.txt`

---

## Python Quick API

### Read Kafka (Consumer)
```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'crypto_raw',
    bootstrap_servers=['localhost:9093'],
    value_deserializer=lambda x: json.loads(x)
)
for msg in consumer:
    print(msg['value'])
```

### Read HDFS (PySpark)
```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Query").getOrCreate()
df = spark.read.parquet("hdfs://namenode:8020/data/crypto/features/")
df.show()
```

### Query MLflow
```python
import mlflow

client = mlflow.tracking.MlflowClient("http://localhost:5000")
models = client.list_registered_models()
for model in models:
    print(model.name)
```

---

## File Locations

- **Producer code**: `kafka/producer.py`
- **Streaming code**: `spark/streaming_job.py`
- **Training code**: `spark/train_model.py`
- **MLflow artifacts**: `mlflow/artifacts/`
- **HDFS data**: `/data/crypto/` (inside namenode)
- **Kafka topics**: 5 topics (raw, clean, features, alerts, predictions)

---

## Useful Documentation Links

- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Spark Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [HDFS User Guide](https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/HdfsUserGuide.html)
- [MLflow Documentation](https://mlflow.org/docs/latest/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

---

## Support

**Problem?** Check in this order:
1. Run `python3 health_check.py`
2. Check logs with `docker-compose logs [service]`
3. Review `DEPLOYMENT_GUIDE.md` troubleshooting section
4. Consult `README.md` detailed documentation

---

**Last Updated**: January 2024
**Quick Reference v1.0**
