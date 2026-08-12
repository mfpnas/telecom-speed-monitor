import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['npx', '--yes', 'fast-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        # Verifica se a saída está vazia
        if not result.stdout.strip():
            print("fast-cli: Saída vazia, tentando novamente...")
            return None
        data = json.loads(result.stdout)
        return {
            'server_id': 'fast_com',
            'sponsor': 'Fast.com (Netflix)',
            'server_name': 'Fast.com Global',
            'distance': 0,
            'ping': 0,
            'download_bps': data.get('downloadSpeed', 0),
            'upload_bps': data.get('uploadSpeed', 0)
        }
    except json.JSONDecodeError as e:
        print(f"fast-cli JSON inválido: {e}")
        return None
    except Exception as e:
        print(f"fast-cli erro: {e}")
        return None