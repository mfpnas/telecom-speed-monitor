import csv
import os
from datetime import datetime
import requests

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return '0.0.0.0'

def write_result(tool_name, result, log_dir):
    os.makedirs(log_dir, exist_ok=True)
    filename = os.path.join(log_dir, f'{tool_name}_speed_logs.csv')
    
    # Adicionar colunas de lat/lon do servidor
    fieldnames = ['Server ID', 'Sponsor', 'Server Name', 'Server Lat', 'Server Lon',
                  'Timestamp', 'Distance', 'Ping', 'Download', 'Upload', 'Share', 'IP Address']
    
    row = {
        'Server ID': result.get('server_id', ''),
        'Sponsor': result.get('sponsor', tool_name),
        'Server Name': result.get('server_name', ''),
        'Server Lat': result.get('server_lat', 0),
        'Server Lon': result.get('server_lon', 0),
        'Timestamp': datetime.utcnow().isoformat() + 'Z',
        'Distance': result.get('distance', 0),
        'Ping': result.get('ping', 0),
        'Download': result.get('download_bps', 0),
        'Upload': result.get('upload_bps', 0),
        'Share': '',
        'IP Address': get_public_ip()
    }
    
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"[{datetime.now()}] {tool_name} -> {filename}")