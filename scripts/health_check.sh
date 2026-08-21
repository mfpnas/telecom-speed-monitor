#!/usr/bin/env bash
# health_check.sh - Verifica saúde dos containers e arquivos de dados

# Configurações
PROJECT_DIR="/home/aurion/Scripts/telecom-speed-monitor"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
DATA_LOG_DIR="$PROJECT_DIR/data/logs"
CONTAINERS=("telecom_collector" "telecom_dashboard")
MAX_AGE_SECONDS=300  # 5 minutos

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "=== Health Check Telecom Speed Monitor ==="

# 1. Verificar containers
for container in "${CONTAINERS[@]}"; do
    if docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null | grep -q true; then
        echo -e "${GREEN}[OK]${NC} Container $container está rodando."
    else
        echo -e "${RED}[FAIL]${NC} Container $container NÃO está rodando. Tentando reiniciar..."
        docker compose -f "$COMPOSE_FILE" up -d "$container"
    fi
done

# 2. Verificar arquivos CSV atualizados
echo ""
echo "Verificando arquivos CSV em $DATA_LOG_DIR ..."
if [ ! -d "$DATA_LOG_DIR" ]; then
    echo -e "${RED}[FAIL]${NC} Diretório de logs não encontrado."
    exit 1
fi

found_issue=0
now=$(date +%s)
for csv_file in "$DATA_LOG_DIR"/*_speed_logs.csv; do
    [ -e "$csv_file" ] || continue
    mtime=$(stat -c %Y "$csv_file")
    age=$((now - mtime))
    if [ "$age" -gt "$MAX_AGE_SECONDS" ]; then
        echo -e "${YELLOW}[WARN]${NC} $csv_file não atualizado há $age segundos (> $MAX_AGE_SECONDS)."
        found_issue=1
    else
        echo -e "${GREEN}[OK]${NC} $csv_file atualizado há $age segundos."
    fi
done

if [ "$found_issue" -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Atenção: alguns arquivos CSV estão desatualizados. Considere reiniciar o coletor.${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}Todos os arquivos atualizados. Sistema saudável.${NC}"
    exit 0
fi