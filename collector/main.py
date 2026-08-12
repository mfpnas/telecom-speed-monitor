import time
import schedule
from collector.config import INTERVAL, LOG_DIR
from collector.utils.logger import write_result
from collector.clients import speedtest_client, librespeed_client, fast_client, iperf_client
from datetime import datetime

def run_all_tests():
    print(f"\n[{datetime.now()}] Starting test round...")
    
    clients = [
        ('speedtest-cli', speedtest_client.run),
        ('librespeed', librespeed_client.run),
        ('fast', fast_client.run),
        ('iperf3', iperf_client.run)
    ]
    
    for name, client_func in clients:
        try:
            result = client_func()
            if result:
                write_result(name, result, LOG_DIR)
            else:
                print(f"[{name}] Failed to get result.")
        except Exception as e:
            print(f"[{name}] Critical error: {e}")

if __name__ == '__main__':
    print(f"Collector started. Interval: {INTERVAL}s. Logs: {LOG_DIR}")
    run_all_tests()
    schedule.every(INTERVAL).seconds.do(run_all_tests)
    
    while True:
        schedule.run_pending()
        time.sleep(1)