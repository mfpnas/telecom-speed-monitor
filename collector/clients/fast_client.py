import subprocess
import json

def run():
    try:
        # Usa npx para executar fast-cli
        result = subprocess.run(
            ['npx', '--yes', 'fast-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
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
    except Exception as e:
        print(f"fast-cli erro: {e}")
        return None