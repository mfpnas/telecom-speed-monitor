import subprocess
import json
import re

def run():
    try:
        # Executa o fast-cli com npx
        result = subprocess.run(
            ['npx', '--yes', 'fast-cli', '--json'],
            capture_output=True,
            text=True,
            timeout=60
        )
        # Verifica se houve erro na execução
        if result.returncode != 0:
            print(f"fast-cli returncode: {result.returncode}")
            print(f"stderr: {result.stderr}")
            return None

        # Tenta fazer o parse do JSON
        output = result.stdout.strip()
        if not output:
            print("fast-cli: saída vazia")
            return None

        data = json.loads(output)
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
        print(f"fast-cli JSON decode error: {e}")
        print(f"Output received: {result.stdout[:200] if result else 'None'}")
        return None
    except Exception as e:
        print(f"fast-cli erro: {e}")
        return None