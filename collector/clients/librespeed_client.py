# collector/clients/librespeed_client.py
import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['librespeed-cli', '--json'],
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

        # O librespeed-cli pode retornar um objeto ou uma lista de objetos
        if isinstance(data, list):
            if not data:
                print("librespeed: empty list")
                return None
            # Usa o primeiro elemento da lista (o mais comum é um único resultado)
            data = data[0]
        elif isinstance(data, dict):
            # Se o objeto tiver uma chave 'results' que é uma lista, usa o primeiro
            if 'results' in data and isinstance(data['results'], list):
                results = data['results']
                if not results:
                    print("librespeed: empty results list")
                    return None
                data = results[0]
        else:
            print(f"librespeed: unexpected JSON type {type(data)}")
            return None

        server = data.get('server', {})
        client = data.get('client', {})

        return {
            'server_id': str(server.get('id', '')),
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
    except subprocess.TimeoutExpired:
        print("librespeed: timeout expired")
        return None
    except Exception as e:
        print(f"librespeed error: {e}")
        return None