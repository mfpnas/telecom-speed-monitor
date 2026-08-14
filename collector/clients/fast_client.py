import subprocess
import json
import ping3
import time

def run():
    """
    Executa o Fast.com (Netflix) para medir download e, complementarmente,
    faz um ping ICMP via ping3 para 8.8.8.8 para obter uma latência aproximada.
    O upload não é medido pelo fast-cli padrão (permanece 0).
    """
    try:
        # Teste Fast.com
        result = subprocess.run(
            ['npx', '--yes', 'fast-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        download_mbps = data.get('downloadSpeed', 0)

        # Ping complementar usando ping3 (puro Python)
        ping_ms = ping3.ping('8.8.8.8', timeout=2)  # retorna None se timeout
        if ping_ms is None:
            ping_ms = 0.0
        else:
            ping_ms = ping_ms * 1000  # converte para milissegundos

        return {
            'server_id': 'fast_com',
            'sponsor': 'Fast.com (Netflix)',
            'server_name': 'Fast.com Global',
            'server_lat': 0,
            'server_lon': 0,
            'distance': 0,
            'ping': ping_ms,
            'download_bps': download_mbps * 1e6,
            'upload_bps': 0,  # fast não mede upload
        }
    except json.JSONDecodeError as e:
        print(f"fast-cli JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"fast-cli error: {e}")
        return None