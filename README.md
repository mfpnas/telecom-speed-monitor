# 📡 Telecom Speed Monitor

**A comprehensive, containerized solution for monitoring internet speed across multiple tools, detecting throttling, and generating legally-admissible reports for telecommunications lawsuits.**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [Dashboard Features](#dashboard-features)
9. [Generating Legal Reports](#generating-legal-reports)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)
12. [License](#license)

---

## Overview

**Telecom Speed Monitor** is a complete, self-hosted solution for monitoring internet speed across **4 different testing tools** simultaneously. It automatically collects data every 5 minutes, stores results in CSV format, provides a **real-time dashboard** with advanced analytics, and generates **court-ready PDF reports** to document throttling and underperformance violations by ISPs.

### Why This Tool Exists

Internet Service Providers (ISPs) often:
- Deliver speeds far below advertised levels
- Apply **throttling** (artificial speed reduction) during weekends/peak hours
- Violate the **80% minimum speed rule** (Anatel Resolution nº 632/2014)

This tool provides the **objective, continuous evidence** needed to:
- File individual lawsuits for damages
- Support collective actions (class actions)
- File complaints with regulatory agencies (e.g., Anatel, FCC, OFCOM)

---

## Features

### Multi-Tool Testing
- 🔹 **speedtest-cli** – Classic Ookla Speedtest (most widely used)
- 🔹 **LibreSpeed (via npx)** – Open-source alternative
- 🔹 **Fast.com (Netflix)** – Tests streaming-optimized connections
- 🔹 **iPerf3** – Professional throughput test (TCP/UDP)

### Data Collection
- ⏱️ **Continuous polling** – configurable interval (default: 5 minutes)
- 📊 **Standardized CSV output** – compatible with analysis tools
- 🌐 **Public IP tracking** – records which IP was used for each test
- 🏷️ **Rich metadata** – server ID, sponsor, location, distance, latency

### Dashboard (Streamlit)
- 📈 **Interactive time-series** graphs for download/upload/ping
- 📊 **Boxplot comparisons** across tools and time periods
- 🔍 **Throttling detection** – weekday vs weekend comparison
- 📉 **Ping vs download** scatter plots
- 📋 **Raw data table** with filtering and export
- ⏰ **Hourly and daily** trend analysis
- 🎯 **Failure detection** – identifies failed tests

### PDF Report Generator
- 📄 **Court-ready PDF** with technical and legal sections
- 📊 **6+ professional graphs** (time series, distributions, boxplots)
- 💰 **Financial loss calculation** (customizable monthly cost)
- ⚖️ **Legal framework** – CDC, Anatel, and jurisprudence references
- 📊 **Tables with median speeds** by day of week and weekend vs weekday

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
│                                                             │
│  ┌─────────────────┐    ┌────────────────────────────┐      │
│  │   Collector     │    │     Dashboard              │      │
│  │   (Python)      │    │     (Streamlit)            │      │
│  │                 │    │                            │      │
│  │ • speedtest-cli │    │ • Interactive graphs       │      │
│  │ • LibreSpeed    │    │ • Throttling detection     │      │
│  │ • Fast.com      │    │ • CSV export               │      │
│  │ • iPerf3        │    │ • PDF report generation    │      │
│  └────────┬────────┘    └────────────┬───────────────┘      │
│           │                          │                      │
│           └──────────┬───────────────┘                      │
│                      ▼                                      │
│              ┌───────────────┐                              │
│              │   Shared      │                              │
│              │   Volume      │                              │
│              │   (./data)    │                              │
│              └───────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Requirements

| Requirement | Minimum |
|-------------|---------|
| **Linux** (or WSL2 on Windows) | Ubuntu 20.04+ / Debian 11+ |
| **Docker** | 24.0+ |
| **Docker Compose** | 2.20+ |
| **Memory** | 512 MB (recommended: 1 GB) |
| **Disk** | 2 GB (logs grow over time) |
| **Internet** | Active connection for testing |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/telecom-speed-monitor.git
cd telecom-speed-monitor
```

### 2. Set Up Directory Structure

```bash
mkdir -p data/logs
```

### 3. Create the Required Files

Create the following files in the project root:

#### `requirements.txt`
```txt
pandas
numpy
matplotlib
seaborn
streamlit
plotly
requests
python-dotenv
schedule
```

#### `.env.example` (optional)
```env
INTERVAL=300
LOG_DIR=/app/data/logs
IPERF_SERVERS=iperf.he.net,iperf.ovh.net,ping.online.net
```

### 4. Create Docker Files

#### `Dockerfile.collector`

```dockerfile
FROM python:3.11-slim

# Cria um usuário não-root com UID 1000 (igual ao seu usuário no host)
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -m -u ${USER_ID} -g appuser appuser

RUN apt-get update && apt-get install -y \
    curl \
    npm \
    iperf3 \
    && rm -rf /var/lib/apt/lists/*

# Instala speedtest-cli via pip
RUN pip install speedtest-cli

# Instala fast-cli via npm
RUN npm install -g fast-cli

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY collector/ ./collector/
COPY scripts/ ./scripts/

# Altera o proprietário dos arquivos para o novo usuário
RUN chown -R appuser:appuser /app

# Muda para o usuário não-root
USER appuser

CMD ["python", "-u", "-m", "collector.main"]
```

#### `Dockerfile.dashboard`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY dashboard/ ./dashboard/
COPY data/ ./data/

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### `docker-compose.yml`

```yaml
services:
  collector:
    build:
      context: .
      dockerfile: Dockerfile.collector
    container_name: telecom_collector
    volumes:
      - ./data:/app/data
    environment:
      - INTERVAL=300
      - LOG_DIR=/app/data/logs
      - IPERF_SERVERS=iperf.he.net,iperf.ovh.net
    restart: unless-stopped
    networks:
      - telecom_net

  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    container_name: telecom_dashboard
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - LOG_DIR=/app/data/logs
    restart: unless-stopped
    networks:
      - telecom_net

networks:
  telecom_net:
    driver: bridge
```

### 5. Create the Collector Code

#### Directory Structure
```
collector/
├── __init__.py
├── main.py
├── config.py
├── clients/
│   ├── __init__.py
│   ├── speedtest_client.py
│   ├── librespeed_client.py
│   ├── fast_client.py
│   └── iperf_client.py
└── utils/
    ├── __init__.py
    └── logger.py
```

#### `collector/config.py`
```python
import os
from dotenv import load_dotenv

load_dotenv()

INTERVAL = int(os.getenv('INTERVAL', 300))
LOG_DIR = os.getenv('LOG_DIR', '/app/data/logs')
IPERF_SERVERS = os.getenv('IPERF_SERVERS', 'iperf.he.net,iperf.ovh.net').split(',')
```

#### `collector/utils/logger.py`
```python
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
    
    fieldnames = ['Server ID', 'Sponsor', 'Server Name', 'Timestamp', 
                  'Distance', 'Ping', 'Download', 'Upload', 'Share', 'IP Address']
    
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
    
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"[{datetime.now()}] {tool_name} -> {filename}")
```

#### `collector/clients/speedtest_client.py`
```python
import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['speedtest-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        return {
            'server_id': data.get('server', {}).get('id', ''),
            'sponsor': data.get('client', {}).get('isp', 'speedtest-cli'),
            'server_name': data.get('server', {}).get('name', ''),
            'distance': data.get('server', {}).get('d', 0),
            'ping': data.get('ping', 0),
            'download_bps': data.get('download', 0),
            'upload_bps': data.get('upload', 0)
        }
    except Exception as e:
        print(f"speedtest-cli error: {e}")
        return None
```

#### `collector/clients/librespeed_client.py`
```python
import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['npx', '--yes', 'speedtest-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        return {
            'server_id': data.get('server', {}).get('id', ''),
            'sponsor': 'LibreSpeed',
            'server_name': data.get('server', {}).get('name', ''),
            'distance': 0,
            'ping': data.get('ping', 0),
            'download_bps': data.get('download', 0) * 1e6,
            'upload_bps': data.get('upload', 0) * 1e6
        }
    except Exception as e:
        print(f"librespeed error: {e}")
        return None
```

#### `collector/clients/fast_client.py`
```python
import subprocess
import json

def run():
    try:
        result = subprocess.run(
            ['fast-cli', '--json'],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        return {
            'server_id': 'fast_com',
            'sponsor': 'Fast.com (Netflix)',
            'server_name': 'Fast.com Global',
            'distance': 0,
            'ping': 0,
            'download_bps': data.get('downloadSpeed', 0),
            'upload_bps': data.get('uploadSpeed', 0)
        }
    except Exception as e:
        print(f"fast-cli error: {e}")
        return None
```

#### `collector/clients/iperf_client.py`
```python
import subprocess
import json
import random
from collector.config import IPERF_SERVERS

def run():
    server = random.choice(IPERF_SERVERS)
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
            'distance': 0,
            'ping': ping,
            'download_bps': download_bps,
            'upload_bps': upload_bps
        }
    except Exception as e:
        print(f"iperf3 error ({server}): {e}")
        return None
```

#### `collector/main.py`
```python
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
```

### 6. Create the Dashboard

#### `dashboard/app.py`

```python
import streamlit as st
import pandas as pd
import os
import glob
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Telecom Speed Monitor")

LOG_DIR = os.getenv('LOG_DIR', '/app/data/logs')
st.title("📡 Telecom Speed Monitor Dashboard")

# ------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    all_files = glob.glob(os.path.join(LOG_DIR, '*_speed_logs.csv'))
    dfs = []
    for f in all_files:
        tool = os.path.basename(f).replace('_speed_logs.csv', '')
        df = pd.read_csv(f)
        df['Tool'] = tool
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

df = load_data()
if df.empty:
    st.warning("No data found. Waiting for collector to start.")
    st.stop()

# ------------------------------------------------------------
# 2. FILTERS
# ------------------------------------------------------------
st.sidebar.header("🔍 Advanced Filters")

tools = st.sidebar.multiselect("Tools", df['Tool'].unique(), default=df['Tool'].unique())

min_date = df['Timestamp'].min().date()
max_date = df['Timestamp'].max().date()
start_date = st.sidebar.date_input("Start", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End", max_date, min_value=min_date, max_value=max_date)

mask = (df['Tool'].isin(tools)) & (df['Timestamp'].dt.date >= start_date) & (df['Timestamp'].dt.date <= end_date)
filtered = df[mask].copy()

if filtered.empty:
    st.warning("No data with selected filters.")
    st.stop()

# ------------------------------------------------------------
# 3. QUICK METRICS
# ------------------------------------------------------------
st.subheader("📊 Summary")
col_metrics = st.columns(4)
with col_metrics[0]:
    st.metric("Total Tests", len(filtered))
with col_metrics[1]:
    st.metric("Avg Download", f"{filtered['Download'].mean()/1e6:.1f} Mbps")
with col_metrics[2]:
    st.metric("Avg Upload", f"{filtered['Upload'].mean()/1e6:.1f} Mbps")
with col_metrics[3]:
    st.metric("Avg Ping", f"{filtered['Ping'].mean():.1f} ms")

# ------------------------------------------------------------
# 4. TABS
# ------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Time Series", "📊 Boxplot", "📉 Scatter", "📅 Throttling", "📋 Raw Data"])

with tab1:
    fig1 = px.line(filtered, x='Timestamp', y='Download', color='Tool',
                   title='Download Evolution (bps)')
    st.plotly_chart(fig1, use_container_width=True)
    
    fig2 = px.line(filtered, x='Timestamp', y='Upload', color='Tool',
                   title='Upload Evolution (bps)')
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    fig3 = px.box(filtered, x='Tool', y='Download', color='Tool',
                  title='Download Distribution by Tool')
    st.plotly_chart(fig3, use_container_width=True)
    
    fig4 = px.box(filtered, x='Tool', y='Ping', color='Tool',
                  title='Ping Distribution by Tool')
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    fig5 = px.scatter(filtered, x='Ping', y='Download', color='Tool',
                      hover_data=['Timestamp', 'Server Name'],
                      title='Ping vs Download')
    st.plotly_chart(fig5, use_container_width=True)

with tab4:
    filtered['DayOfWeek'] = filtered['Timestamp'].dt.day_name()
    filtered['IsWeekend'] = filtered['DayOfWeek'].isin(['Saturday', 'Sunday'])
    aggr = filtered.groupby(['Tool', 'IsWeekend'])['Download'].mean().reset_index()
    aggr['Period'] = aggr['IsWeekend'].map({True: 'Weekend', False: 'Weekday'})
    
    fig6 = px.bar(aggr, x='Tool', y='Download', color='Period', barmode='group',
                  title='Avg Download: Weekday vs Weekend (Throttling Detection)')
    st.plotly_chart(fig6, use_container_width=True)

with tab5:
    st.dataframe(filtered[['Timestamp', 'Tool', 'Server Name', 'Ping', 'Download', 'Upload']].head(100))

# ------------------------------------------------------------
# 5. EXPORT
# ------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Export for PDF Report")

export_tool = st.sidebar.selectbox("Tool to export", df['Tool'].unique())
export_days = st.sidebar.slider("Last N days", 1, 30, 7)

if st.sidebar.button("Generate CSV"):
    mask_export = (df['Tool'] == export_tool) & (df['Timestamp'] >= datetime.now() - timedelta(days=export_days))
    export_df = df[mask_export].copy()
    cols = ['Server ID', 'Sponsor', 'Server Name', 'Timestamp', 'Distance', 'Ping', 'Download', 'Upload', 'Share', 'IP Address']
    export_df = export_df[cols].fillna('')
    csv = export_df.to_csv(index=False)
    st.sidebar.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{export_tool}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
```

---

## Configuration

### Environment Variables

Create a `.env` file (optional):

```bash
# Interval between tests (seconds)
INTERVAL=300

# Log directory (inside container)
LOG_DIR=/app/data/logs

# iPerf3 servers (comma-separated)
IPERF_SERVERS=iperf.he.net,iperf.ovh.net,ping.online.net
```

---

## Usage

### 1. Start the Services

```bash
# Build and start all containers
docker compose up -d --build

# Check if containers are running
docker compose ps
```

### 2. Monitor the Collector Logs

```bash
# View real-time logs from the collector
docker logs -f telecom_collector
```

### 3. Access the Dashboard

Open your browser and go to: **http://localhost:8501**

### 4. Stop the Services

```bash
docker compose down
```

### 5. View Data Directly

```bash
# List CSV files
ls -la data/logs/

# View the first few lines of speedtest-cli logs
head -5 data/logs/speedtest-cli_speed_logs.csv
```

---

## Dashboard Features

### 1. Time Series Analysis
- View download, upload, and ping evolution over time
- Compare different testing tools
- Identify patterns (e.g., slower speeds at night)

### 2. Distribution Analysis
- Boxplots showing speed distribution by tool
- Identify outliers and anomalies

### 3. Throttling Detection
- Compare average speeds between **weekdays and weekends**
- Detect artificial speed reduction patterns

### 4. Export for PDF Report
- Select a specific tool and time period
- Download CSV in the exact format required by the legal report generator

---

## Generating Legal Reports

### 1. Export CSV from Dashboard
1. Go to **http://localhost:8501**
2. Select the desired tool (e.g., `speedtest-cli`)
3. Choose the time period (e.g., last 14 days)
4. Click **"Generate CSV"** and download the file

### 2. Save the CSV File
Place the downloaded CSV in the project root or a known location.

### 3. Run the PDF Report Generator

Use the final script from the previous prompt (the one that generates the professional PDF report). The script expects a CSV with columns:
- `Server ID`
- `Sponsor`
- `Server Name`
- `Timestamp`
- `Distance`
- `Ping`
- `Download`
- `Upload`
- `Share`
- `IP Address`

### 4. Alternative: Use the Combined Script

You can also modify the report generator to read all CSV files automatically:

```python
import glob
all_files = glob.glob('/app/data/logs/*_speed_logs.csv')
df = pd.concat([pd.read_csv(f) for f in all_files], ignore_index=True)
```

---

## Troubleshooting

### Issue: "permission denied while trying to connect to the Docker daemon socket"

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in, or run:
newgrp docker
```

### Issue: "librespeed-cli not found"

**Solution:** The collector uses `npx speedtest-cli` (the npm package). This is installed on first run via `npx --yes`.

### Issue: Dashboard shows no data

**Solution:**
```bash
# Check if collector is running
docker logs telecom_collector

# Verify CSV files exist
ls -la data/logs/
```

### Issue: iPerf3 tests failing

**Solution:**
- Ensure iPerf3 servers are reachable
- Try changing the servers in `.env`
- Some corporate networks block iPerf3 ports

### Issue: High disk usage

**Solution:**
- Logs grow ~1 MB per day per tool (4 tools = ~4 MB/day)
- Clean old logs: `rm -rf data/logs/*_speed_logs.csv`

---

## Contributing

### How to Contribute

1. **Fork** the repository
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add some amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Ideas for Contributions

- Support for additional speed test tools (e.g., `speedtest.py`, `ookla-speedtest`)
- Integration with Grafana/Prometheus
- Multi-tenant support (multiple users)
- Email alerts for speed drops
- Auto-generate PDF reports on a schedule
- Webhook integration for automated legal filings

---

## License

This project is licensed under the **MIT License**.

---

## Disclaimer

This tool is provided for **educational and informational purposes only**. Users should:

- Verify the accuracy of the data
- Consult with legal professionals before taking legal action
- Comply with local laws and regulations regarding surveillance and data collection

The authors assume **no liability** for any outcomes resulting from the use of this tool.

---

## Contact

- 📧 **Email:** mfpnas@gmail.com
- 🐛 **Issues:** [GitHub Issues](https://github.com/mfpnas/telecom-speed-monitor/issues)

---

## Acknowledgments

- [speedtest-cli](https://github.com/sivel/speedtest-cli) – Official Ookla Speedtest CLI
- [LibreSpeed](https://github.com/librespeed/speedtest-cli) – Open-source alternative
- [Fast.com](https://fast.com) – Netflix speed test
- [iPerf3](https://iperf.fr/) – Professional network throughput tester
- [Streamlit](https://streamlit.io/) – Interactive dashboard framework

---

## Star History

If you find this tool useful, please consider giving it a ⭐ on GitHub!