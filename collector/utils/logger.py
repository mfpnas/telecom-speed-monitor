# collector/utils/logger.py
import os
import csv
from datetime import datetime

def write_result(tool_name: str, result: dict, log_dir: str):
    """Escreve o resultado de um teste no arquivo CSV apropriado."""
    os.makedirs(log_dir, exist_ok=True)
    filepath = os.path.join(log_dir, f"{tool_name}_speed_logs.csv")
    fieldnames = [
        'Server ID', 'Sponsor', 'Server Name', 'Server Lat', 'Server Lon',
        'Timestamp', 'Distance', 'Ping', 'Download', 'Upload', 'Share', 'IP Address'
    ]
    file_exists = os.path.isfile(filepath)
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        row = {
            'Server ID': result.get('server_id', ''),
            'Sponsor': result.get('sponsor', ''),
            'Server Name': result.get('server_name', ''),
            'Server Lat': result.get('server_lat', 0),
            'Server Lon': result.get('server_lon', 0),
            'Timestamp': datetime.utcnow().isoformat() + 'Z',
            'Distance': result.get('distance', 0),
            'Ping': result.get('ping', 0),
            'Download': result.get('download_bps', 0),
            'Upload': result.get('upload_bps', 0),
            'Share': result.get('share', ''),
            'IP Address': result.get('ip_address', '')
        }
        writer.writerow(row)