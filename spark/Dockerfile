FROM python:3.9-slim

# Install Java
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python packages
RUN pip install --no-cache-dir --no-compile \
    pyspark==3.5.0 \
    kafka-python==2.0.2 \
    mlflow==2.10.0 \
    numpy==1.24.3 \
    pandas==2.0.3

COPY requirements.txt .
RUN cat requirements.txt

COPY *.py ./

CMD ["python3", "-u", "streaming_job.py"]
