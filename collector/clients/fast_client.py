# collector/clients/fast_client.py
import subprocess
import json
import re
import ping3

def run():
    try:
        result = subprocess.run(
            ['npx', '--yes', 'fast-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"fast-cli returncode: {result.returncode}")
            print(f"stderr: {result.stderr}")
            return None

        output = result.stdout.strip()
        if not output:
            print("fast-cli: empty output")
            return None

        try:
            data = json.loads(output)
            download_mbps = data.get('downloadSpeed', 0)
        except json.JSONDecodeError:
            # Tenta extrair de texto simples (ex: "123.45 Mbps")
            match = re.search(r'([\d.]+)\s*Mbps', output)
            download_mbps = float(match.group(1)) if match else 0
            print(f"fast-cli: parsed speed from text: {download_mbps} Mbps")

        ping_ms = ping3.ping('8.8.8.8', timeout=2)
        ping_ms = ping_ms * 1000 if ping_ms else 0.0

        return {
            'server_id': 'fast_com',
            'sponsor': 'Fast.com (Netflix)',
            'server_name': 'Fast.com Global',
            'server_lat': 0,
            'server_lon': 0,
            'distance': 0,
            'ping': ping_ms,
            'download_bps': download_mbps * 1e6,
            'upload_bps': 0,
        }
    except subprocess.TimeoutExpired:
        print("fast-cli: timeout expired")
        return None
    except Exception as e:
        print(f"fast-cli error: {e}")
        return None