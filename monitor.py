#!/usr/bin/env python3
"""
Monitoramento para Telecom Speed Monitor.
Verifica containers, inicia/reinicia se necessário, e valida coleta de dados.
"""
import os
import time
import subprocess
import logging
from datetime import datetime
import requests

# Configurações
LOG_FILE = "/var/log/telecom-monitor/monitor.log"
CONTAINERS = ["telecom_collector", "telecom_dashboard"]
CSV_FILES = ["speedtest-cli_speed_logs.csv", "librespeed_speed_logs.csv", "fast_speed_logs.csv", "iperf3_speed_logs.csv"]
DASHBOARD_URL = "http://localhost:8501"
CSV_TIMEOUT_SECONDS = 600  # 10 minutos
PROJECT_DIR = "/home/aurion/Scripts/telecom_monitor"

# Configurar logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log(msg, level='info'):
    getattr(logging, level)(msg)

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def container_exists(name):
    stdout, _, rc = run_cmd(f"docker ps -a --format '{{{{.Names}}}}' | grep -w '{name}'")
    return rc == 0 and name in stdout

def container_running(name):
    stdout, _, rc = run_cmd(f"docker ps --format '{{{{.Names}}}}' | grep -w '{name}'")
    return rc == 0 and name in stdout

def start_container(name):
    log(f"Iniciando container {name}...", 'warning')
    # Tenta iniciar com docker start (se existir parado)
    stdout, stderr, rc = run_cmd(f"docker start {name}")
    if rc == 0:
        time.sleep(5)
        if container_running(name):
            log(f"Container {name} iniciado com sucesso.", 'info')
            return True
    # Se falhar, tenta up com compose
    stdout, stderr, rc = run_cmd(f"docker compose -f {PROJECT_DIR}/docker-compose.yml up -d {name}")
    if rc == 0:
        time.sleep(5)
        if container_running(name):
            log(f"Container {name} criado e iniciado via compose.", 'info')
            return True
    log(f"Falha ao iniciar {name}: {stderr}", 'error')
    return False

def restart_container(name):
    if container_running(name):
        log(f"Reiniciando container {name}...", 'warning')
        stdout, stderr, rc = run_cmd(f"docker restart {name}")
        if rc != 0:
            log(f"Falha ao reiniciar {name}: {stderr}", 'error')
            return False
        time.sleep(5)
        if container_running(name):
            log(f"Container {name} reiniciado com sucesso.", 'info')
            return True
    else:
        log(f"Container {name} não está rodando.", 'warning')
        return start_container(name)

def check_collector_files():
    log_dir = os.path.join(PROJECT_DIR, "data/logs")
    now = datetime.now()
    for fname in CSV_FILES:
        filepath = os.path.join(log_dir, fname)
        if not os.path.exists(filepath):
            log(f"Arquivo {fname} não encontrado.", 'warning')
            return False
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        age = (now - mtime).total_seconds()
        if age > CSV_TIMEOUT_SECONDS:
            log(f"Arquivo {fname} não atualizado há {age:.0f} segundos.", 'warning')
            return False
    return True

def check_dashboard():
    try:
        r = requests.get(DASHBOARD_URL, timeout=5)
        return r.status_code == 200
    except:
        return False

def main():
    log("=== Iniciando verificação ===")

    # 1. Garantir que os containers existam e estejam rodando
    for container in CONTAINERS:
        if not container_running(container):
            log(f"Container {container} não está rodando.", 'error')
            start_container(container)
        else:
            log(f"Container {container} está rodando.", 'info')

    # 2. Verificar coleta de dados
    if container_running("telecom_collector"):
        if not check_collector_files():
            log("Coleta de dados não está gerando arquivos recentes.", 'error')
            restart_container("telecom_collector")
        else:
            log("Coleta de dados está funcionando.", 'info')

    # 3. Verificar dashboard
    if not check_dashboard():
        log("Dashboard não está respondendo.", 'error')
        restart_container("telecom_dashboard")
    else:
        log("Dashboard está respondendo.", 'info')

    log("=== Verificação concluída ===\n")

if __name__ == "__main__":
    main()