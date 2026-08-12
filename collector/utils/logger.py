import csv
import os
from datetime import datetime
import socket

def get_public_ip():
    try:
        import requests
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return '0.0.0.0'

def write_result(tool_name, result, log_dir):
    """Escreve resultado no CSV padronizado para a ferramenta."""
    os.makedirs(log_dir, exist_ok=True)
    filename = os.path.join(log_dir, f'{tool_name}_speed_logs.csv')
    
    # Cabeçalho compatível com o script do relatório
    fieldnames = ['Server ID', 'Sponsor', 'Server Name', 'Timestamp', 
                  'Distance', 'Ping', 'Download', 'Upload', 'Share', 'IP Address']
    
    # Preenche os dados
    row = {
        'Server ID': result.get('server_id', ''),
        'Sponsor': result.get('sponsor', tool_name),
        'Server Name': result.get('server_name', ''),
        'Timestamp': datetime.utcnow().isoformat() + 'Z',
        'Distance': result.get('distance', 0),
        'Ping': result.get('ping', 0),
        'Download': result.get('download_bps', 0),
        'Upload': result.get('upload_bps', 0),
        'Share': '',
        'IP Address': get_public_ip()
    }
    
    # Escreve (append ou cria)
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"[{datetime.now()}] {tool_name} -> {filename}")