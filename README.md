# 📡 Telecom Speed Monitor

**Monitoramento contínuo de velocidade de internet, detecção de throttling e geração de relatórios jurídicos prontos para ação judicial contra provedores (em conformidade com a Anatel).**

---

## 📖 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Funcionalidades](#funcionalidades)
4. [Pré-requisitos](#pré-requisitos)
5. [Instalação](#instalação)
6. [Configuração](#configuração)
7. [Execução](#execução)
8. [Monitoramento e Saúde](#monitoramento-e-saúde)
9. [Gerando Relatórios](#gerando-relatórios)
10. [Estrutura de Diretórios](#estrutura-de-diretórios)
11. [Como Contribuir](#como-contribuir)
12. [Licença](#licença)

---

## Visão Geral

O **Telecom Speed Monitor** é uma solução completa e auto-hospedada que:

- Realiza testes contínuos de velocidade usando **quatro ferramentas** (`speedtest-cli`, `LibreSpeed`, `Fast.com` e `iPerf3`).
- Armazena os resultados em CSVs padronizados, com geolocalização dos servidores.
- Oferece um **dashboard interativo** (Streamlit) com gráficos, detecção de throttling e exportação de dados.
- Gera **relatórios PDF juridicamente admissíveis** que documentam a entrega insuficiente de velocidade e a prática de throttling, embasados na **Resolução Anatel nº 632/2014** (mínimo de 80% da velocidade contratada).

O projeto foi desenvolvido pensando no **consumidor brasileiro**, mas pode ser adaptado para qualquer jurisdição onde seja necessário comprovar a má prestação de serviços de internet.

---

## Arquitetura


┌──────────────────────────────────────────┐
│              Docker Compose              │
│                                          │
│┌─────────────────┐ ┌────────────────────┐│
││   Collector     │ │  Dashboard         ││
││   (Python)      │ │  (Streamlit)       ││
││                 │ │                    ││
││ • speedtest-cli │ │ • Visualização     ││
││ • LibreSpeed    │ │ • Filtros/gráficos ││
││ • Fast.com      │ │ • Throttling       ││
││ • iPerf3        │ │ • Relatórios PDF   ││
│└────────┬────────┘ └─────────────┬──────┘│
│         │                        │       │
│         └──────────┬─────────────┘       │
│                    ▼                     │
│            ┌──────────────┐              │
│            │   Volume     │              │
│            │   ./data     │              │
│            │   (CSVs)     │              │
│            └──────────────┘              │
└──────────────────────────────────────────┘


---

## Funcionalidades

### 🔬 Testes Multi‑Ferramenta
- **speedtest-cli** (Ookla) – confiável e amplamente usado.
- **LibreSpeed** – código aberto, geo‑aware.
- **Fast.com** (Netflix) – otimizado para streaming (apenas download, com ping via `ping3`).
- **iPerf3** – teste profissional de throughput (TCP/UDP).

### 📊 Coleta e Armazenamento
- Execução contínua a cada 5 minutos (configurável).
- Padronização de campos e geolocalização dos servidores.
- Logs em CSV com metadados (IP público, servidor, distância, latência).

### 📈 Dashboard (Streamlit)
- Séries temporais com zoom e slider.
- Boxplots comparativos entre ferramentas.
- Detecção de throttling (comparativo dias úteis vs. fins de semana).
- Mapa de servidores utilizados.
- Tabela com dados brutos e coluna "Tipo de Teste".
- Atualização automática (1, 5 ou 10 minutos).

### 📄 Gerador de Relatórios PDF
- Estrutura **profissional e jurídica** (11 páginas fixas, formato A4 retrato).
- Capa, sumário, objetivo, metodologia, análise estatística, comparação contratado vs. entregue, cálculo de perda financeira, fundamentação legal, recomendações, anexos com gráficos comparativos, resumo executivo.
- Gráficos comparativos entre **speedtest-cli e LibreSpeed** (as ferramentas mais confiáveis).
- Cálculo de perdas financeiras individuais e estimativa para ação civil pública.
- **Totalmente em português**, com formatação de moeda brasileira.

### 🛡️ Monitoramento de Saúde (Opcional)
- Script `monitor.py` que verifica containers e arquivos CSV a cada minuto (via systemd timer).
- Reinicia containers automaticamente se pararem ou se os CSVs não forem atualizados.
- Logs em `/var/log/telecom-monitor/monitor.log`.

---

## Pré-requisitos

- **Linux** (Ubuntu/Debian recomendado) ou WSL2 no Windows.
- **Docker** (24.0+) e **Docker Compose** (2.20+).
- **Memória**: 1 GB RAM (512 MB mínimo).
- **Armazenamento**: 2 GB (para logs e CSVs).
- **Conexão com a internet** (para os testes).

---

## Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/mfpnas/telecom-speed-monitor.git
cd telecom-speed-monitor
```

### 2. Crie a estrutura de diretórios
```bash
mkdir -p data/logs
```

### 3. (Opcional) Configure variáveis de ambiente
Crie um arquivo `.env` na raiz com:
```env
INTERVAL=300
LOG_DIR=/app/data/logs
IPERF_SERVERS=iperf-ams-nl.eranium.net,lon.speedtest.clouvider.net,speedtest.uztelecom.uz
```

### 4. Construa e inicie os containers
```bash
docker compose up -d --build
```

### 5. Acesse o dashboard
Abra `http://localhost:8501` no navegador.

---

## Configuração

### Variáveis de Ambiente (`.env`)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `INTERVAL` | Intervalo entre rodadas de teste (segundos) | `300` |
| `LOG_DIR` | Diretório de logs (dentro do container) | `/app/data/logs` |
| `IPERF_SERVERS` | Lista de servidores iPerf3 (separados por vírgula) | `iperf-ams-nl.eranium.net,lon.speedtest.clouvider.net,speedtest.uztelecom.uz` |

### Arquivos Docker

- `Dockerfile.collector` – imagem do coletor.
- `Dockerfile.dashboard` – imagem do dashboard.
- `docker-compose.yml` – orquestração dos serviços.

---

## Execução

### Iniciar todos os serviços
```bash
docker compose up -d
```

### Parar todos os serviços
```bash
docker compose down
```

### Visualizar logs do coletor
```bash
docker logs -f telecom_collector
```

### Visualizar logs do dashboard
```bash
docker logs -f telecom_dashboard
```

---

## Monitoramento e Saúde

Recomenda‑se configurar o monitor automático para garantir que o sistema esteja sempre funcionando.

### 1. Criar o serviço systemd

**Arquivo:** `/etc/systemd/system/telecom-monitor.service`
```ini
[Unit]
Description=Telecom Monitor Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
User=seu-usuario
Group=seu-usuario
WorkingDirectory=/home/seu-usuario/telecom-speed-monitor
ExecStart=/usr/bin/python3 /home/seu-usuario/telecom-speed-monitor/scripts/monitor.py
StandardOutput=append:/var/log/telecom-monitor/monitor.log
StandardError=append:/var/log/telecom-monitor/monitor.log
```

**Arquivo:** `/etc/systemd/system/telecom-monitor.timer`
```ini
[Unit]
Description=Run telecom monitor every minute

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min

[Install]
WantedBy=timers.target
```

### 2. Habilitar e iniciar
```bash
sudo systemctl daemon-reload
sudo systemctl enable telecom-monitor.timer
sudo systemctl start telecom-monitor.timer
```

### 3. Rotação de logs
Crie `/etc/logrotate.d/telecom-monitor` com:
```
/var/log/telecom-monitor/monitor.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 644 usuario usuario
    sharedscripts
    postrotate
        systemctl kill -s USR1 telecom-monitor.service 2>/dev/null || true
    endscript
}
```

---

## Gerando Relatórios

### Pelo Dashboard
1. Acesse `http://localhost:8501`.
2. Preencha os dados pessoais, ISP, plano e período.
3. Clique em **Generate PDF Report**.
4. Faça o download do PDF gerado.

### Pela Linha de Comando (manual)
```bash
docker exec -it telecom_dashboard python /app/scripts/generate_pdf_report.py \
    --csv /app/data/logs/speedtest-cli_speed_logs.csv \
    --client "Mauricio Faria Palma Nascimento" \
    --isp "VIVO" \
    --plan "VIVO TOTAL – PRO (500/250 Mbps)" \
    --address "Guaxupé, MG, Brasil" \
    --output /app/data/logs/relatorio_manual.pdf
```

O PDF será salvo em `data/logs/relatorio_manual.pdf`.

---

## Estrutura de Diretórios

Após a refatoração, a estrutura do projeto ficou assim:

```
telecom-speed-monitor/
├── collector/                      # Coletor de dados
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   ├── main.py
│   └── clients/
│       ├── __init__.py
│       ├── speedtest_client.py
│       ├── librespeed_client.py
│       ├── fast_client.py
│       └── iperf_client.py
│
├── dashboard/                      # Dashboard Streamlit
│   ├── __init__.py
│   ├── app.py                      # Interface principal
│   ├── data_loader.py              # Carregamento de dados
│   ├── filters.py                  # Filtros
│   └── report_generator.py         # Interface para gerar PDF
│
├── report/                         # Geração de relatórios PDF
│   ├── __init__.py
│   ├── generate_pdf.py             # Função principal
│   ├── pdf_builder.py              # Construção do documento
│   ├── sections.py                 # Criação de cada seção
│   ├── plots.py                    # Gráficos comparativos
│   ├── stats.py                    # Cálculos estatísticos
│   └── formatters.py               # Formatação BR
│
├── scripts/                        # Scripts auxiliares
│   └── monitor.py                  # Health check
│
├── generate_pdf_report.py          # Wrapper CLI
├── app.py                          # Wrapper para o dashboard (ponto de entrada)
├── docker-compose.yml
├── Dockerfile.collector
├── Dockerfile.dashboard
├── requirements.txt
├── .env.example
└── README.md
```

---

## Como Contribuir

1. **Fork** o repositório.
2. Crie uma branch para sua feature: `git checkout -b feature/minha-feature`.
3. Commit suas alterações: `git commit -m 'Adiciona nova feature'`.
4. Push para a branch: `git push origin feature/minha-feature`.
5. Abra um **Pull Request** descrevendo suas alterações.

---

## Licença

Este projeto está licenciado sob a **MIT License**. Consulte o arquivo `LICENSE` para mais detalhes.

**Disclaimer**: A ferramenta é fornecida apenas para fins educacionais e informativos. O usuário é responsável por verificar a precisão dos dados e consultar profissionais jurídicos antes de tomar qualquer ação legal. Os autores não se responsabilizam por quaisquer consequências do uso deste software.

---

**Desenvolvido com ❤️ para consumidores que exigem transparência de seus provedores de internet.**