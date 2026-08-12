import os
from dotenv import load_dotenv

load_dotenv()

INTERVAL = int(os.getenv('INTERVAL', 300))
LOG_DIR = os.getenv('LOG_DIR', '/app/data/logs')
IPERF_SERVERS = os.getenv('IPERF_SERVERS', 'iperf.he.net,iperf.ovh.net').split(',')