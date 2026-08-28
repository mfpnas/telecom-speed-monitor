# collector/clients/librespeed_client.py
import subprocess
import json

def run():
    """
    Executa o librespeed-cli e retorna os resultados padronizados em bps.
    Detecta automaticamente se os valores de download/upload estão em Mbps ou bps.
    """
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

        # Normaliza a estrutura: pode ser dict, lista, ou dict com chave 'results'
        if isinstance(data, list):
            if not data:
                print("librespeed: empty list")
                return None
            data = data[0]
        elif isinstance(data, dict):
            if 'results' in data and isinstance(data['results'], list):
                results = data['results']
                if not results:
                    print("librespeed: empty results list")
                    return None
                data = results[0]
        else:
            print(f"librespeed: unexpected JSON type {type(data)}")
            return None

        # Extrai informações do servidor com valores padrão
        server = data.get('server', {}) or {}
        if not isinstance(server, dict):
            server = {}

        # Função auxiliar para converter para bps se necessário
        def to_bps(value):
            try:
                val = float(value)
            except (TypeError, ValueError):
                return 0
            # Se o valor é menor que 100000, provavelmente está em Mbps
            if val < 100000:
                return int(val * 1e6)
            return int(val)

        # Monta o dicionário padronizado
        return {
            'server_id': str(server.get('id', '')),
            'sponsor': server.get('sponsor', 'LibreSpeed'),
            'server_name': server.get('name', ''),
            'server_lat': float(server.get('lat', 0) or 0),
            'server_lon': float(server.get('lon', 0) or 0),
            'distance': float(server.get('d', 0) or 0),
            'ping': float(data.get('ping', 0) or 0),
            'download_bps': to_bps(data.get('download', 0)),
            'upload_bps': to_bps(data.get('upload', 0)),
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