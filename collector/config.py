import os
from dotenv import load_dotenv

load_dotenv()

INTERVAL = int(os.getenv('INTERVAL', 300))
LOG_DIR = os.getenv('LOG_DIR', '/app/data/logs')   # <--- CORRIGIDO
IPERF_SERVERS = os.getenv('IPERF_SERVERS', 'iperf-ams-nl.eranium.net,lon.speedtest.clouvider.net,speedtest.uztelecom.uz').split(',')