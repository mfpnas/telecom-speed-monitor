import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['speedtest-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        return {
            'server_id': data.get('server', {}).get('id', ''),
            'sponsor': data.get('client', {}).get('isp', 'speedtest-cli'),
            'server_name': data.get('server', {}).get('name', ''),
            'distance': data.get('server', {}).get('d', 0),
            'ping': data.get('ping', 0),
            'download_bps': data.get('download', 0),
            'upload_bps': data.get('upload', 0)
        }
    except Exception as e:
        print(f"speedtest-cli erro: {e}")
        return None