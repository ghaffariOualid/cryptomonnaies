import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from kafka import KafkaConsumer
import json
import time
import os
from datetime import datetime
import mlflow
from mlflow.tracking import MlflowClient

# Page Config
st.set_page_config(
    page_title="Crypto Big Data Monitor",
    page_icon="🪙",
    layout="wide"
)

# Configuration
KAFKA_BOOTSTRAP = "kafka:29092"
HDFS_FEATURES_PATH = "/data/crypto/features"  # Mounted volume path
MLFLOW_URI = "http://mlflow:5000"

st.title("🪙 Real-Time Crypto Big Data Pipeline")

# --- Sidebar: System Status ---
st.sidebar.header("System Status")
status_placeholder = st.sidebar.empty()

def check_system_health():
    """Check if critical services are reachable"""
    health = {"Kafka": "🔴", "HDFS Data": "🔴", "MLflow": "🔴"}
    
    # Check Kafka
    try:
        consumer = KafkaConsumer(bootstrap_servers=KAFKA_BOOTSTRAP)
        if consumer.bootstrap_connected():
            health["Kafka"] = "🟢"
        consumer.close()
    except:
        pass

    # Check HDFS (via mounted volume)
    if os.path.exists(HDFS_FEATURES_PATH) and len(os.listdir(HDFS_FEATURES_PATH)) > 0:
        health["HDFS Data"] = "🟢"
    
    # Check MLflow
    try:
        mlflow.set_tracking_uri(MLFLOW_URI)
        client = MlflowClient()
        client.search_experiments()
        health["MLflow"] = "🟢"
    except:
        pass
        
    return health

health_status = check_system_health()
status_placeholder.markdown(f"""
- **Kafka Broker:** {health_status['Kafka']}
- **Spark Output (HDFS):** {health_status['HDFS Data']}
- **MLflow Server:** {health_status['MLflow']}
""")

# --- Tabs for different views ---
tab1, tab2, tab3 = st.tabs(["📈 Real-Time Stream", "⚠️ Anomaly Alerts", "🤖 Model Performance"])

# ==========================================
# TAB 1: Live Data (From Kafka)
# ==========================================
with tab1:
    st.subheader("Live Market Data (Reading from Kafka: crypto_raw)")
    
    col1, col2, col3 = st.columns(3)
    metric_price = col1.empty()
    metric_vol = col2.empty()
    metric_symbol = col3.empty()
    
    chart_placeholder = st.empty()
    
    # Initialize session state for data buffer
    if 'data_buffer' not in st.session_state:
        st.session_state.data_buffer = pd.DataFrame(columns=['timestamp', 'symbol', 'price'])

    # Button to refresh/start stream
    if st.button("Refresh Live Data"):
        try:
            # FIX: Use 'earliest' to grab data immediately
            consumer = KafkaConsumer(
                'crypto_raw',
                bootstrap_servers=KAFKA_BOOTSTRAP,
                auto_offset_reset='earliest',  # <--- CHANGED FROM 'latest'
                enable_auto_commit=False,      # <--- Don't "read" the message forever
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=1000       # <--- Short timeout is fine now
            )
            
            new_data = []
            for message in consumer:
                record = message.value
                new_data.append({
                    'timestamp': record.get('timestamp'),
                    'symbol': record.get('symbol'),
                    'price': record.get('price')
                })
            
            if new_data:
                df_new = pd.DataFrame(new_data)
                df_new['timestamp'] = pd.to_datetime(df_new['timestamp'])
                st.session_state.data_buffer = pd.concat([st.session_state.data_buffer, df_new]).tail(100)
                
                # Update Metrics (Latest Record)
                latest = st.session_state.data_buffer.iloc[-1]
                metric_symbol.metric("Symbol", latest['symbol'])
                metric_price.metric("Price", f"${latest['price']:,.2f}")
                
                # Update Chart
                fig = px.line(st.session_state.data_buffer, x='timestamp', y='price', color='symbol', title="Live Price Feed")
                chart_placeholder.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Waiting for data from Producer...")
                
        except Exception as e:
            st.error(f"Kafka Error: {e}")

# ==========================================
# TAB 2: Alerts (From Kafka)
# ==========================================
with tab2:
    st.subheader("🚨 Real-Time Anomaly Alerts (Topic: crypto_alerts)")
    
    alerts_container = st.container()
    
    if st.button("Check for Alerts"):
        try:
            consumer_alerts = KafkaConsumer(
                'crypto_alerts',
                bootstrap_servers=KAFKA_BOOTSTRAP,
                auto_offset_reset='earliest', # Show history of alerts
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=2000
            )
            
            alerts = []
            for message in consumer_alerts:
                alerts.append(message.value)
            
            if alerts:
                df_alerts = pd.DataFrame(alerts)
                st.dataframe(df_alerts)
                
                # Alert Distribution Chart
                fig_alerts = px.bar(df_alerts, x='symbol', y='anomaly_score', 
                                  color='is_price_anomaly', title="Anomaly Severity by Coin")
                st.plotly_chart(fig_alerts)
            else:
                st.success("✅ No anomalies detected recently. Market is stable.")
                
        except Exception as e:
            st.error(f"Could not fetch alerts: {e}")

# ==========================================
# TAB 3: Model & Features (From MLflow & HDFS)
# ==========================================
with tab3:
    st.subheader("🤖 Model Training & Feature Analysis")
    
    # 1. Show Historical Features from HDFS
    st.markdown("### 1. Engineered Features (Reading Parquet from HDFS)")
    
    if os.path.exists(HDFS_FEATURES_PATH):
        try:
            # Simple recursive search for parquet files
            parquet_files = []
            for root, dirs, files in os.walk(HDFS_FEATURES_PATH):
                for file in files:
                    if file.endswith(".parquet"):
                        parquet_files.append(os.path.join(root, file))
            
            if parquet_files:
                # Read a sample of the latest file
                latest_file = parquet_files[0] 
                df_features = pd.read_parquet(latest_file)
                st.write(f"Preview of latest features data ({len(parquet_files)} part-files found):")
                st.dataframe(df_features.head(10))
                
                # Feature Correlation
                if 'price_mean' in df_features.columns:
                    st.markdown("#### Price vs Volatility Correlation")
                    fig_corr = px.scatter(df_features, x='price_mean', y='price_stddev', color='symbol')
                    st.plotly_chart(fig_corr)
            else:
                st.warning("No Parquet files found in feature directory yet.")
        except Exception as e:
            st.error(f"Error reading HDFS files: {e}")
    else:
        st.error(f"HDFS path not found: {HDFS_FEATURES_PATH}")

    # 2. Show MLflow Experiments
    st.markdown("### 2. MLflow Experiment Tracking")
    try:
        experiments = mlflow.search_experiments()
        if experiments:
            exp_data = []
            for exp in experiments:
                exp_data.append({"Name": exp.name, "ID": exp.experiment_id, "Artifact Loc": exp.artifact_location})
            st.table(pd.DataFrame(exp_data))
            st.markdown(f"[Open MLflow UI]({MLFLOW_URI})")
        else:
            st.info("No experiments found yet.")
    except:
        st.warning("Could not connect to MLflow server.")

# Auto-refresh note
st.sidebar.markdown("---")
st.sidebar.caption("Click buttons to refresh data. Auto-refresh can be enabled via loops if needed.")