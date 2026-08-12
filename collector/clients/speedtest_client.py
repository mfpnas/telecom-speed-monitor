import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['speedtest-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        server = data.get('server', {})
        return {
            'server_id': server.get('id', ''),
            'sponsor': data.get('client', {}).get('isp', 'speedtest-cli'),
            'server_name': server.get('name', ''),
            'server_lat': float(server.get('lat', 0)),
            'server_lon': float(server.get('lon', 0)),
            'distance': float(server.get('d', 0)),
            'ping': data.get('ping', 0),
            'download_bps': data.get('download', 0),
            'upload_bps': data.get('upload', 0)
        }
    except Exception as e:
        print(f"speedtest-cli error: {e}")
        return None