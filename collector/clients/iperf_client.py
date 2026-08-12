import subprocess
import json
import random
from collector.config import IPERF_SERVERS

# Lista de fallback com servidores confiáveis do repositório R0GGER
# Fonte: https://github.com/R0GGER/public-iperf3-servers
DEFAULT_SERVERS = [
    # América do Sul
    "speedtest.uztelecom.uz",        # América do Sul[reference:12]
    # Fallback para Europa (caso os da América do Sul falhem)
    "iperf-ams-nl.eranium.net",      # Amsterdam[reference:13]
    "lon.speedtest.clouvider.net",   # London[reference:14]
]

def run():
    # Tenta usar servidores do .env primeiro, depois fallback
    servers = IPERF_SERVERS if IPERF_SERVERS and len(IPERF_SERVERS) > 0 else DEFAULT_SERVERS
    server = random.choice(servers)
    
    try:
        # Teste de Download
        result_dl = subprocess.run(
            ['iperf3', '-c', server, '-J', '-t', '10'],
            capture_output=True, text=True, timeout=60
        )
        data_dl = json.loads(result_dl.stdout)
        download_bps = data_dl.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)
        
        # Teste de Upload (modo reverso)
        result_ul = subprocess.run(
            ['iperf3', '-c', server, '-J', '-t', '10', '-R'],
            capture_output=True, text=True, timeout=60
        )
        data_ul = json.loads(result_ul.stdout)
        upload_bps = data_ul.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)
        
        # Extrai jitter como proxy de ping
        ping = data_dl.get('end', {}).get('streams', [{}])[0].get('sender', {}).get('jitter_ms', 0)
        
        return {
            'server_id': 'iperf3',
            'sponsor': 'iPerf3',
            'server_name': server,
            'distance': 0,
            'ping': ping,
            'download_bps': download_bps,
            'upload_bps': upload_bps
        }
    except subprocess.TimeoutExpired:
        print(f"iperf3 timeout: {server}")
        return None
    except json.JSONDecodeError as e:
        print(f"iperf3 JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"iperf3 error ({server}): {e}")
        return None