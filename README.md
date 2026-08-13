# 📡 Telecom Speed Monitor

**A complete, self‑hosted solution to monitor internet speed, detect throttling, and generate court‑ready PDF reports for lawsuits against ISPs (Brazilian Anatel standard).**

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Why This Tool Exists](#why-this-tool-exists)
3. [Features](#features)
4. [Architecture](#architecture)
5. [Prerequisites](#prerequisites)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Running the System](#running-the-system)
9. [Monitoring & Health Checks](#monitoring--health-checks)
10. [Generating Legal Reports](#generating-legal-reports)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)
13. [License & Disclaimer](#license--disclaimer)

---

## Overview

**Telecom Speed Monitor** continuously tests your internet connection using **four different tools** (`speedtest-cli`, `LibreSpeed`, `Fast.com`, and `iPerf3`). It stores the results in a standardized CSV format, provides a **real‑time dashboard** with advanced analytics, and generates **professional, legally‑admissible PDF reports** to document underperformance and throttling by Internet Service Providers (ISPs).

> 🇧🇷 This tool was designed with **Brazilian consumers** in mind, using the **Anatel Resolution nº 632/2014** as a reference (minimum 80% of advertised speed). It is equally useful in any jurisdiction where documented evidence of throttling is needed.

---

## Why This Tool Exists

Internet Service Providers often:
- Deliver speeds **far below** what they advertise.
- Apply **throttling** (artificial speed reduction) during weekends or peak hours.
- Violate the **minimum speed rules** set by regulators (e.g., Anatel’s 80% rule).

This tool provides the **objective, continuous evidence** required to:
- **File individual lawsuits** for financial compensation.
- **Support collective actions** (class actions) on behalf of many consumers.
- **Complain to regulatory agencies** (Anatel, FCC, etc.).

---

## Features

### 🔬 Multi‑Tool Testing
| Tool                | Description |
|---------------------|-------------|
| `speedtest-cli`     | Classic Ookla Speedtest (the most widely used) |
| `LibreSpeed`        | Open‑source alternative (via `npx`) |
| `Fast.com`          | Netflix’s streaming‑optimised test |
| `iPerf3`            | Professional TCP/UDP throughput test |

### 📊 Data Collection & Storage
- Continuous polling (default interval: 5 minutes).
- Standardised CSV output (compatible with other analysis tools).
- Public IP tracking and rich metadata (server location, distance, latency).

### 📈 Interactive Dashboard (Streamlit)
- **Time‑series graphs** with zoom and range sliders.
- **Boxplot comparisons** between testing tools.
- **Throttling detection** – compares weekday vs weekend speeds.
- **Ping vs Download** scatter plots.
- **Server location map** (for tools that provide geolocation).
- **Raw data table** with filtering and export.
- **Auto‑refresh** (1, 5, or 10 minutes).

### 📄 PDF Report Generator
- **Court‑ready PDF** structure (cover, objective, methodology, statistics, legal framework).
- **6+ professional graphs** (time series, distributions, boxplots, map, hourly and daily averages).
- **Financial loss calculation** – computes how much you overpaid.
- **Brazilian legal references** (CDC, LGT, Anatel, and jurisprudence).
- **Tables with median speeds** by day of week and weekend vs weekday.
- **Dynamic filename**: `YYYYMMDD_ISP_Client_Start-End.pdf`.

### 🛡️ Health Monitoring (Optional)
- **Systemd timer** runs a script every minute.
- Detects if containers stop or files are not updated.
- **Auto‑corrects** by restarting containers.
- **Logs** all actions to `/var/log/telecom-monitor/monitor.log`.

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         Docker Compose                            │
│                                                                   │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐  │
│  │   Collector         │    │      Dashboard                   │  │
│  │   (Python)          │    │      (Streamlit)                 │  │
│  │                     │    │                                  │  │
│  │  • speedtest-cli    │    │  • Time‑series graphs            │  │
│  │  • LibreSpeed       │    │  • Throttling detection          │  │
│  │  • Fast.com         │    │  • CSV export                    │  │
│  │  • iPerf3           │    │  • PDF report generation         │  │
│  └─────────┬───────────┘    └──────────────┬───────────────────┘  │
│            │                                │                     │
│            └────────────┬───────────────────┘                     │
│                         ▼                                         │
│                  ┌───────────────┐                                │
│                  │   Shared      │                                │
│                  │   Volume      │                                │
│                  │   (./data)    │                                │
│                  │   (CSV logs)  │                                │
│                  └───────────────┘                                │
└───────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

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

### 2. Create the `data/logs` Directory

```bash
mkdir -p data/logs
```

### 3. (Optional) Adjust Environment Variables

Copy the sample environment file and edit it:

```bash
cp .env.example .env
nano .env
```

Common settings:
- `INTERVAL`: seconds between test rounds (default: 300).
- `IPERF_SERVERS`: comma‑separated list of iPerf3 servers.

### 4. Build and Start the Containers

```bash
docker compose up -d --build
```

This will:
- Build the `collector` and `dashboard` images.
- Start both containers.
- Mount the `./data` folder inside the containers at `/app/data`.

---

## Configuration

### Environment Variables (`./.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `INTERVAL` | Time between test rounds (seconds) | `300` |
| `LOG_DIR` | Where CSV logs are stored (inside container) | `/app/data/logs` |
| `IPERF_SERVERS` | Comma‑separated list of iPerf3 servers | `iperf-ams-nl.eranium.net,lon.speedtest.clouvider.net,speedtest.uztelecom.uz` |

### Docker Compose (`docker-compose.yml`)

- The `collector` service runs the speed tests.
- The `dashboard` service serves the Streamlit app on port `8501`.
- Both share the `./data` volume.
- The `restart: unless‑stopped` policy ensures they restart after a host reboot.

---

## Running the System

### Start All Services

```bash
docker compose up -d
```

### Check Container Status

```bash
docker ps
```

### View Collector Logs

```bash
docker logs -f telecom_collector
```

### Access the Dashboard

Open your browser and go to:

```
http://localhost:8501
```

### Stop the System

```bash
docker compose down
```

---

## Monitoring & Health Checks

For long‑term (e.g., 45‑day) operations, we strongly recommend enabling the built‑in health monitor.

### 1. Create the Monitoring Script

The script `monitor.py` is already in the repository. It:
- Checks every minute if the containers are running.
- If a container is down, it restarts it.
- Checks if CSV files are being updated (10‑minute timeout).
- Logs everything to `/var/log/telecom-monitor/monitor.log`.

### 2. Set Up Systemd Timer (Recommended)

Create the service and timer files:

#### `/etc/systemd/system/telecom-monitor.service`
```ini
[Unit]
Description=Telecom Monitor Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
User=aurion
Group=aurion
WorkingDirectory=/home/aurion/Scripts/telecom_monitor
ExecStart=/usr/bin/python3 /home/aurion/Scripts/telecom_monitor/monitor.py
StandardOutput=append:/var/log/telecom-monitor/monitor.log
StandardError=append:/var/log/telecom-monitor/monitor.log
```

#### `/etc/systemd/system/telecom-monitor.timer`
```ini
[Unit]
Description=Run telecom monitor every minute

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min

[Install]
WantedBy=timers.target
```

Enable and start the timer:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telecom-monitor.timer
sudo systemctl start telecom-monitor.timer
```

### 3. Log Rotation

Create `/etc/logrotate.d/telecom-monitor` to rotate the monitor logs:

```
/var/log/telecom-monitor/monitor.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 aurion aurion
    sharedscripts
    postrotate
        systemctl kill -s USR1 telecom-monitor.service 2>/dev/null || true
    endscript
}
```

---

## Generating Legal Reports

### Via the Dashboard (Recommended)

1. Open `http://localhost:8501`.
2. Select the desired **time period** and **tools**.
3. Fill in your personal information (Client, ISP, Plan, Address).
4. Click **Generate PDF Report**.
5. Download the PDF.

### Via Command Line (Manual)

```bash
docker exec -it telecom_dashboard python /app/scripts/generate_pdf_report.py \
    --csv /app/data/logs/speedtest-cli_speed_logs.csv \
    --client "Mauricio Faria Palma Nascimento" \
    --isp "VIVO" \
    --plan "VIVO TOTAL – PRO (500/250 Mbps)" \
    --address "Guaxupé, MG, Brazil" \
    --output /app/data/logs/relatorio_manual.pdf
```

The PDF will appear in `data/logs/relatorio_manual.pdf`.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Permission denied for Docker** | Add your user to the `docker` group: `sudo usermod -aG docker $USER` and log out/in. |
| **Dashboard shows no data** | Check that the collector is running and has written CSV files. Wait 5 minutes for the first test. |
| **librespeed returns huge numbers** | Uncheck `librespeed` in the dashboard filter. This tool sometimes selects servers that return inconsistent data. The other three tools are usually more reliable. |
| **iPerf3 tests fail** | Check the servers in `.env`. Some public iPerf servers block high‑volume tests. Try changing to `iperf-ams-nl.eranium.net`. |
| **PDF generation fails** | Ensure the CSV file exists and is not empty. Check `docker logs telecom_dashboard` for detailed errors. |
| **High disk usage** | Logs and CSVs accumulate. The monitor rotates logs; you can manually remove old CSVs: `rm -rf data/logs/*.csv`. |

---

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository.
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`).
3. **Commit your changes** (`git commit -m 'Add amazing feature'`).
4. **Push to the branch** (`git push origin feature/amazing-feature`).
5. **Open a Pull Request**.

Ideas for improvement:
- Add more speed test tools (e.g., `speedtest‑py`, `ookla‑speedtest`).
- Integrate with Grafana/Prometheus.
- Add email alerts for speed drops.
- Support multiple users (multi‑tenant).

---

## License & Disclaimer

This project is licensed under the **MIT License**.

**Disclaimer**: This tool is provided **for educational and informational purposes only**. Users should:
- Verify the accuracy of the data.
- Consult with legal professionals before taking any legal action.
- Comply with local laws regarding data collection.

The authors assume **no liability** for any outcomes resulting from the use of this software.

---