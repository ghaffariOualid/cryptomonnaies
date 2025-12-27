# DEPLOYMENT_GUIDE.md - Complete Deployment Instructions

## 🎯 Deployment Checklist

### Pre-Deployment

- [ ] Docker & Docker Compose installed (`docker --version`, `docker-compose --version`)
- [ ] 8GB+ RAM available
- [ ] 20GB free disk space
- [ ] Ports 9092, 8080, 8081, 9870, 5000 not in use
- [ ] Python 3.10+ available
- [ ] Git installed

### Step 1: Verify System Requirements

```bash
# Check Docker
docker --version
# Expected: Docker version 20.10+

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 1.29+

# Check RAM
# Linux/macOS:
free -h | grep Mem

# Windows (PowerShell):
Get-WmiObject -Class Win32_ComputerSystem | Select-Object TotalPhysicalMemory
# Should be 8GB+
```

### Step 2: Clone Repository

```bash
cd ~
git clone https://github.com/yourusername/crypto-bigdata-platform.git
cd crypto-bigdata-platform
```

### Step 3: Create Required Directories

```bash
# Create MLflow directories
mkdir -p mlflow/mlruns mlflow/artifacts

# Create HDFS directories
mkdir -p hdfs/data

# Verify structure
ls -la mlflow/ hdfs/
```

### Step 4: Build Docker Images

```bash
# Build all services
docker-compose build --no-cache

# Verify images
docker images | grep crypto
```

### Step 5: Start Services

```bash
# Start all services in background
docker-compose up -d

# Monitor startup (watch for "healthy" status)
watch docker-compose ps

# Or one-time check
docker-compose ps
```

**Expected Output**:
```
NAME                 IMAGE               STATUS
zookeeper           confluentinc/...    Up (healthy)
kafka               confluentinc/...    Up (healthy)
kafka-ui            provectuslabs/...   Up
namenode            bde2020/...         Up (healthy)
datanode            bde2020/...         Up (healthy)
spark-master        bitnami/spark:...   Up
spark-worker-1      bitnami/spark:...   Up
mlflow              ghcr.io/mlflow/...  Up
crypto-producer     crypto-producer     Up
spark-streaming     spark-streaming     Up
```

### Step 6: Verify Services

```bash
# Run health check
python3 health_check.py

# Expected output:
# ✅ All systems HEALTHY
```

### Step 7: Check Data Flow

```bash
# 1. Check if messages are in Kafka
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto_raw \
  --from-beginning \
  --max-messages 5 \
  --timeout-ms 5000

# 2. Verify HDFS has data
docker-compose exec namenode hadoop fs -ls /data/crypto/clean/

# 3. Check Spark streaming job
docker-compose logs spark-streaming | tail -20
```

### Step 8: Access Web Interfaces

Open in browser:

1. **Kafka UI** → http://localhost:8080
   - Verify topics exist
   - Check message flow

2. **Spark Master** → http://localhost:8081
   - Check cluster health
   - View running applications

3. **HDFS Namenode** → http://localhost:9870
   - Browse file system
   - Check storage

4. **MLflow** → http://localhost:5000
   - View experiments
   - Track runs

---

## 🧪 Testing

### Test 1: Producer is sending data

```bash
# Check logs
docker-compose logs crypto-producer | grep "📤"

# Expected: Multiple "📤 Sent" messages
```

### Test 2: Streaming pipeline is active

```bash
# Check Spark streaming logs
docker-compose logs spark-streaming | grep "Spark session"

# Expected: "✅ Spark session created successfully"
```

### Test 3: Data in HDFS

```bash
# Count records in clean data
docker-compose exec namenode hadoop fs -count /data/crypto/clean/

# Expected: Non-zero count
```

### Test 4: Anomalies being detected

```bash
# Read alert messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic crypto_alerts \
  --from-beginning \
  --timeout-ms 10000
```

---

## 🤖 Train ML Models

### Option 1: Manual Training

```bash
# Submit training job
docker-compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --total-executor-cores 4 \
  --executor-memory 2g \
  --driver-memory 2g \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  /app/spark/train_model.py
```

### Option 2: Scheduled Training (Cron)

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cd ~/crypto-bigdata-platform && docker-compose exec spark-master spark-submit /app/spark/train_model.py
```

### Option 3: View Training Results

```bash
# Open MLflow dashboard
# http://localhost:5000

# Compare models and promote to production
```

---

## 🔍 Monitoring & Debugging

### Check Logs

```bash
# Specific service
docker-compose logs crypto-producer -f      # Follow producer logs
docker-compose logs spark-streaming -f      # Follow streaming
docker-compose logs kafka -f                 # Follow Kafka

# All services
docker-compose logs -f
```

### Common Issues

#### Issue: Kafka Producer can't connect

```bash
# Check Kafka logs
docker-compose logs kafka | grep -i error

# Verify network
docker-compose exec kafka nc -zv kafka 29092
```

#### Issue: HDFS permissions error

```bash
# Reset permissions
docker-compose exec namenode hadoop fs -chmod -R 777 /data/
```

#### Issue: Spark streaming crashes

```bash
# Check Spark logs
docker-compose logs spark-streaming | tail -50

# Check HDFS connectivity
docker-compose exec spark-master hadoop fs -ls /data/crypto/
```

---

## 🛑 Shutdown

### Graceful Shutdown

```bash
# Stop all services (data preserved)
docker-compose down

# Remove volumes too (CLEAN START)
docker-compose down -v

# Verify cleanup
docker-compose ps
# Should show: "No running services"
```

---

## 📊 Performance Tuning

### Increase Processing Power

Edit `docker-compose.yml`:

```yaml
spark-worker-1:
  environment:
    SPARK_WORKER_MEMORY: 4G    # Increase from 2G
    SPARK_WORKER_CORES: 4      # Increase from 2
```

Then:
```bash
docker-compose up -d spark-worker-1
```

### Increase Kafka Partitions

```bash
# Increase from 3 to 6 partitions
docker-compose exec kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --alter \
  --topic crypto_raw \
  --partitions 6
```

---

## 🔐 Production Hardening

### Enable Authentication

1. **Kafka SASL/SSL**
   - Update broker configuration
   - Use certificates from Let's Encrypt

2. **HDFS Kerberos**
   - Setup KDC
   - Configure Kerberos principals

3. **MLflow Auth**
   - Use reverse proxy (Nginx)
   - Enable basic authentication

### Network Security

```yaml
# In docker-compose.yml
networks:
  crypto_network:
    internal: false  # Allow external access if needed
```

---

## 📈 Scaling Considerations

### Horizontal Scaling

Add more Spark workers:

```yaml
spark-worker-2:
  image: bitnami/spark:3.5.0
  environment:
    SPARK_MODE: worker
    SPARK_MASTER_URL: spark://spark-master:7077
    SPARK_WORKER_MEMORY: 2G
    SPARK_WORKER_CORES: 2
```

### Vertical Scaling

Increase resource limits in `docker-compose.yml`:

```yaml
services:
  spark-master:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## 📝 Backup & Recovery

### Backup MLflow Models

```bash
# Backup MLflow directory
tar -czf mlflow_backup_$(date +%s).tar.gz mlflow/

# Backup HDFS data
docker-compose exec namenode hadoop fs -get /data/crypto /backup/
```

### Restore from Backup

```bash
# Restore MLflow
tar -xzf mlflow_backup_*.tar.gz

# Restore HDFS
docker-compose exec namenode hadoop fs -put /backup/crypto /data/
```

---

## ✅ Deployment Validation Checklist

- [ ] All containers are running
- [ ] Kafka topics created successfully
- [ ] Producer is sending messages
- [ ] Streaming job is consuming data
- [ ] Data being written to HDFS
- [ ] MLflow tracking working
- [ ] Web UIs accessible
- [ ] No errors in logs
- [ ] Health check passing

---

## 🆘 Support & Troubleshooting

See [README.md](README.md) for:
- Detailed component documentation
- API examples
- Monitoring guide
- Performance metrics

---

**Last Updated**: January 2024
**Version**: 1.0
