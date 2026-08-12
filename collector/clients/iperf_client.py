import subprocess
import json
import random
import time
from collector.config import IPERF_SERVERS

def run():
    # Lista de servidores padrão (caso não definidos no .env)
    default_servers = ['iperf.he.net', 'iperf.ovh.net', 'ping.online.net']
    servers = IPERF_SERVERS if IPERF_SERVERS else default_servers
    
    # Embaralha para distribuir a carga
    shuffled = servers.copy()
    random.shuffle(shuffled)
    
    for server in shuffled:
        try:
            print(f"Tentando iperf3 com servidor: {server}")
            
            # Teste de download
            result_dl = subprocess.run(
                ['iperf3', '-c', server, '-J', '-t', '8'],
                capture_output=True, text=True, timeout=90
            )
            if result_dl.returncode != 0:
                print(f"iperf3 download falhou para {server}: {result_dl.stderr[:100]}")
                continue
                
            data_dl = json.loads(result_dl.stdout)
            download_bps = data_dl.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)
            
            # Teste de upload (com -R)
            result_ul = subprocess.run(
                ['iperf3', '-c', server, '-J', '-t', '8', '-R'],
                capture_output=True, text=True, timeout=90
            )
            if result_ul.returncode != 0:
                print(f"iperf3 upload falhou para {server}: {result_ul.stderr[:100]}")
                continue
                
            data_ul = json.loads(result_ul.stdout)
            upload_bps = data_ul.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)
            
            # Extrai jitter (ping aproximado)
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
            print(f"iperf3 timeout para {server} (90s)")
            continue
        except json.JSONDecodeError as e:
            print(f"iperf3 JSON decode error para {server}: {e}")
            continue
        except Exception as e:
            print(f"iperf3 erro ({server}): {e}")
            continue
    
    # Se nenhum servidor funcionou, retorna None
    print("Todos os servidores iperf3 falharam.")
    return None