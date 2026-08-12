import subprocess
import json
import random
from collector.config import IPERF_SERVERS

DEFAULT_SERVERS = [
    "speedtest.uztelecom.uz",
    "iperf-ams-nl.eranium.net",
    "lon.speedtest.clouvider.net",
]

def run():
    servers = IPERF_SERVERS if IPERF_SERVERS and len(IPERF_SERVERS) > 0 else DEFAULT_SERVERS
    server = random.choice(servers)
    try:
        result_dl = subprocess.run(
            ['iperf3', '-c', server, '-J', '-t', '10'],
            capture_output=True, text=True, timeout=60
        )
        data_dl = json.loads(result_dl.stdout)
        download_bps = data_dl.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)
        
        result_ul = subprocess.run(
            ['iperf3', '-c', server, '-J', '-t', '10', '-R'],
            capture_output=True, text=True, timeout=60
        )
        data_ul = json.loads(result_ul.stdout)
        upload_bps = data_ul.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)
        
        ping = data_dl.get('end', {}).get('streams', [{}])[0].get('sender', {}).get('jitter_ms', 0)
        
        return {
            'server_id': 'iperf3',
            'sponsor': 'iPerf3',
            'server_name': server,
            'server_lat': 0,
            'server_lon': 0,
            'distance': 0,
            'ping': ping,
            'download_bps': download_bps,
            'upload_bps': upload_bps
        }
    except subprocess.TimeoutExpired:
        print(f"iperf3 timeout: {server}")
        return None
    except Exception as e:
        print(f"iperf3 error ({server}): {e}")
        return None