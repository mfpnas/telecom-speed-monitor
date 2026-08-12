import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['npx', '--yes', 'speedtest-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        download_mbps = data.get('download', 0)
        upload_mbps = data.get('upload', 0)
        return {
            'server_id': data.get('server', {}).get('id', ''),
            'sponsor': 'LibreSpeed',
            'server_name': data.get('server', {}).get('name', ''),
            'distance': 0,
            'ping': data.get('ping', 0),
            'download_bps': download_mbps * 1e6,
            'upload_bps': upload_mbps * 1e6
        }
    except Exception as e:
        print(f"librespeed error: {e}")
        return None