import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['npx', '--yes', 'speedtest-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"librespeed returncode: {result.returncode}")
            print(f"stderr: {result.stderr}")
            return None

        output = result.stdout.strip()
        if not output:
            print("librespeed: empty output")
            return None

        data = json.loads(output)
        server = data.get('server', {})
        client = data.get('client', {})

        return {
            'server_id': server.get('id', ''),
            'sponsor': server.get('sponsor', 'LibreSpeed'),
            'server_name': server.get('name', ''),
            'server_lat': float(server.get('lat', 0)),
            'server_lon': float(server.get('lon', 0)),
            'distance': float(server.get('d', 0)),
            'ping': data.get('ping', 0),
            'download_bps': data.get('download', 0),   # já em bps
            'upload_bps': data.get('upload', 0),       # já em bps
        }
    except json.JSONDecodeError as e:
        print(f"librespeed JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"librespeed error: {e}")
        return None