import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['npx', '--yes', 'speedtest-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        return {
            'server_id': data.get('server', {}).get('id', ''),
            'sponsor': 'LibreSpeed',
            'server_name': data.get('server', {}).get('name', ''),
            'distance': 0,
            'ping': data.get('ping', 0),
            'download_bps': data.get('download', 0) * 1e6,
            'upload_bps': data.get('upload', 0) * 1e6
        }
    except Exception as e:
        print(f"librespeed erro: {e}")
        return None
