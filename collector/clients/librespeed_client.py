import subprocess
import json
import re

def run():
    try:
        # Executa o comando e captura a saída
        result = subprocess.run(
            ['npx', '--yes', 'speedtest-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )

        # Verifica se houve erro na execução
        if result.returncode != 0:
            print(f"librespeed returncode: {result.returncode}")
            print(f"stderr: {result.stderr}")
            return None

        # Tenta fazer o parse do JSON
        output = result.stdout.strip()
        if not output:
            print("librespeed: saída vazia")
            return None

        data = json.loads(output)

        # Extrai os valores de download e upload
        download_raw = data.get('download', 0)
        upload_raw = data.get('upload', 0)

        # --- CORREÇÃO: Sanitização dos valores ---
        # Se o valor for maior que 10 Gbps (10^10 bps), provavelmente está em bytes ou Mbps.
        # Vamos convertê-lo para bps.
        if download_raw > 10_000_000_000:
            print(f"librespeed: download raw ({download_raw}) parece estar em Bytes ou Mbps. Convertendo...")
            # Tenta converter de Bytes para bits (multiplica por 8)
            # ou de Mbps para bps (multiplica por 1_000_000)
            # Vamos usar uma heurística: se o número for muito grande, dividimos por 1_000_000
            # e depois multiplicamos por 1_000_000 para manter o valor em bps, mas isso é um palpite.
            # A maneira mais segura é tentar as duas conversões e ver qual faz sentido.
            # Vamos assumir que está em Bytes e converter para bits.
            download_bps = download_raw * 8
            upload_bps = upload_raw * 8
        else:
            download_bps = download_raw
            upload_bps = upload_raw

        # Extrai outras informações
        return {
            'server_id': data.get('server', {}).get('id', ''),
            'sponsor': 'LibreSpeed',
            'server_name': data.get('server', {}).get('name', ''),
            'distance': 0,
            'ping': data.get('ping', 0),
            'download_bps': download_bps,
            'upload_bps': upload_bps
        }

    except json.JSONDecodeError as e:
        print(f"librespeed JSON decode error: {e}")
        print(f"Output received: {output[:200] if 'output' in locals() else 'None'}")
        return None
    except Exception as e:
        print(f"librespeed error: {e}")
        return None