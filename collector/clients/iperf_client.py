import subprocess
import json
import random
import ping3
from collector.config import IPERF_SERVERS

DEFAULT_SERVERS = [
    "speedtest.uztelecom.uz",
    "iperf-ams-nl.eranium.net",
    "lon.speedtest.clouvider.net",
]

def run():
    servers = IPERF_SERVERS if IPERF_SERVERS and len(IPERF_SERVERS) > 0 else DEFAULT_SERVERS
    random.shuffle(servers)
    server = servers[0]

    try:
        result_dl = subprocess.run(
            ['iperf3', '-c', server, '-J', '-t', '8'],
            capture_output=True, text=True, timeout=80
        )
        data_dl = json.loads(result_dl.stdout)
        download_bps = data_dl.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)

        result_ul = subprocess.run(
            ['iperf3', '-c', server, '-J', '-t', '8', '-R'],
            capture_output=True, text=True, timeout=80
        )
        data_ul = json.loads(result_ul.stdout)
        upload_bps = data_ul.get('end', {}).get('sum_received', {}).get('bits_per_second', 0)

        ping_ms = 0.0
        if download_bps == 0 and upload_bps == 0:
            ping_result = ping3.ping(server, timeout=2)
            if ping_result is not None:
                ping_ms = ping_result * 1000
        else:
            ping_ms = data_dl.get('end', {}).get('streams', [{}])[0].get('sender', {}).get('jitter_ms', 0)

        return {
            'server_id': 'iperf3',
            'sponsor': 'iPerf3',
            'server_name': server,
            'server_lat': 0,
            'server_lon': 0,
            'distance': 0,
            'ping': ping_ms,
            'download_bps': download_bps,
            'upload_bps': upload_bps
        }
    except subprocess.TimeoutExpired:
        print(f"iperf3 timeout: {server}")
        return None
    except json.JSONDecodeError as e:
        print(f"iperf3 JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"iperf3 error ({server}): {e}")
        return None