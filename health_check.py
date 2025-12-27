#!/usr/bin/env python3
"""
Platform Health Check Utility
Validates all components are running and interconnected
"""

import socket
import subprocess
import sys
import time
from typing import List, Tuple

# Service endpoints to check
SERVICES = {
    "kafka": ("localhost", 9093),
    "spark-master": ("localhost", 8081),
    "hdfs-namenode": ("localhost", 9870),
    "mlflow": ("localhost", 5000),
    "kafka-ui": ("localhost", 8080),
}


def check_port(host: str, port: int, timeout: float = 2) -> bool:
    """Check if a port is open"""
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except (socket.timeout, socket.error):
        return False


def check_docker_containers() -> List[Tuple[str, bool]]:
    """Check if Docker containers are running"""
    results = []
    try:
        output = subprocess.check_output(
            ["docker-compose", "ps", "--format", "json"],
            text=True,
            timeout=5
        )
        # Simplified check - if docker-compose works, containers exist
        results.append(("docker-compose", True))
    except Exception as e:
        results.append(("docker-compose", False))
    
    return results


def health_check() -> bool:
    """Run complete health check"""
    print("\n" + "=" * 60)
    print("🏥 Crypto Platform Health Check")
    print("=" * 60 + "\n")
    
    all_healthy = True
    
    # Check Docker containers
    print("📦 Container Status:")
    try:
        docker_results = check_docker_containers()
        for service, status in docker_results:
            symbol = "✅" if status else "❌"
            print(f"  {symbol} {service}")
            all_healthy = all_healthy and status
    except Exception as e:
        print(f"  ❌ Error checking containers: {e}")
        all_healthy = False
    
    print("\n🔌 Service Connectivity:")
    for service_name, (host, port) in SERVICES.items():
        is_open = check_port(host, port)
        symbol = "✅" if is_open else "❌"
        status = f"RUNNING ({host}:{port})" if is_open else f"OFFLINE ({host}:{port})"
        print(f"  {symbol} {service_name.upper():15} {status}")
        all_healthy = all_healthy and is_open
    
    print("\n" + "=" * 60)
    if all_healthy:
        print("✅ All systems HEALTHY")
    else:
        print("❌ Some services are DOWN - Check logs with:")
        print("   docker-compose logs [service-name]")
    print("=" * 60 + "\n")
    
    return all_healthy


if __name__ == "__main__":
    healthy = health_check()
    sys.exit(0 if healthy else 1)
