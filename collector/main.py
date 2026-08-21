# collector/main.py
import time
import schedule
import logging
from datetime import datetime
from collector.config import INTERVAL, LOG_DIR
from collector.utils.logger import write_result
from collector.clients import speedtest_client, librespeed_client, fast_client, iperf_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_all_tests():
    logging.info("Starting test round...")
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
                logging.info(f"{name}: OK")
            else:
                logging.warning(f"{name}: Failed to get result.")
        except Exception as e:
            logging.error(f"{name}: Critical error - {e}")

if __name__ == '__main__':
    logging.info(f"Collector started. Interval: {INTERVAL}s. Logs: {LOG_DIR}")
    run_all_tests()
    schedule.every(INTERVAL).seconds.do(run_all_tests)
    while True:
        schedule.run_pending()
        time.sleep(1)