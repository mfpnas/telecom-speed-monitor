#!/usr/bin/env python3
# scripts/monitor.py
import subprocess
import os
import time
import logging
from datetime import datetime

LOG_FILE = "/var/log/telecom-monitor/monitor.log"
DATA_DIR = "./data"
CONTAINERS = ["telecom_collector", "telecom_dashboard"]

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def check_containers():
    """Verifica se os containers estão em execução."""
    for container in CONTAINERS:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            capture_output=True, text=True
        )
        if result.returncode != 0 or result.stdout.strip() != "true":
            logging.error(f"Container {container} não está em execução. Reiniciando...")
            subprocess.run(["docker", "compose", "up", "-d", container])

def check_data_files():
    """Verifica se os CSVs foram atualizados nos últimos 5 minutos."""
    log_dir = os.path.join(DATA_DIR, "logs")
    if not os.path.isdir(log_dir):
        logging.error("Diretório de logs não existe.")
        return
    now = time.time()
    for file in os.listdir(log_dir):
        if file.endswith("_speed_logs.csv"):
            path = os.path.join(log_dir, file)
            mtime = os.path.getmtime(path)
            if now - mtime > 300:  # 5 minutos
                logging.warning(f"Arquivo {file} não atualizado há mais de 5 minutos.")

def main():
    logging.info("Monitor executado.")
    check_containers()
    check_data_files()

if __name__ == "__main__":
    main()