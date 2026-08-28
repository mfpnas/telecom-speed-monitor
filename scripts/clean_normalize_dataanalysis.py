#!/usr/bin/env python3
"""
Script de Limpeza, Normalização e Análise dos Dados do Telecom Speed Monitor.

Executa:
1. Carrega todos os CSVs do diretório de logs.
2. Limpa dados inválidos (download/upload <= 0, ping > 10000, etc.).
3. Normaliza unidades (converte Mbps para bps se necessário).
4. Gera análises e estatísticas.
5. Gera um resumo em texto.

Uso:
    python scripts/clean_normalize_dataanalysis.py
    python scripts/clean_normalize_dataanalysis.py /caminho/para/logs
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime, timezone


def load_data(log_dir: str = "/app/data/logs") -> pd.DataFrame:
    """Carrega todos os CSVs e adiciona a coluna 'Tool'."""
    all_files = glob.glob(os.path.join(log_dir, '*_speed_logs.csv'))
    dfs = []
    for f in all_files:
        tool = os.path.basename(f).replace('_speed_logs.csv', '')
        try:
            df = pd.read_csv(f)
        except pd.errors.ParserError:
            df = pd.read_csv(f, on_bad_lines='skip')
        if df.empty:
            continue
        df['Tool'] = tool
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
        elif 'timestamp' in df.columns:
            df.rename(columns={'timestamp': 'Timestamp'}, inplace=True)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
        else:
            mtime = os.path.getmtime(f)
            df['Timestamp'] = pd.to_datetime(mtime, unit='s', utc=True)
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def clean_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e normaliza os dados.
    - Converte valores que estão em Mbps para bps.
    - Remove registros inválidos (Download/Upload <= 0, Ping > 10000).
    - Converte colunas numéricas para float.
    """
    df = df.copy()
    
    # Converter colunas numéricas para float
    num_cols = ['Download', 'Upload', 'Ping']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Função para detectar e converter Mbps para bps
    def to_bps(value):
        if pd.isna(value) or value == 0:
            return value
        # Se o valor for menor que 100000, assume que está em Mbps
        if abs(value) < 100000:
            return value * 1e6
        return value
    
    # Aplicar conversão apenas se necessário (detecta valores extremamente baixos)
    # Se a média de Download for < 100000, aplica conversão
    if 'Download' in df.columns and 'Upload' in df.columns:
        avg_dl = df['Download'].mean()
        avg_ul = df['Upload'].mean()
        if avg_dl < 100000 or avg_ul < 100000:
            df['Download'] = df['Download'].apply(to_bps)
            df['Upload'] = df['Upload'].apply(to_bps)
    
    # Remover registros inválidos
    if 'Download' in df.columns:
        df = df[df['Download'] > 0]
    if 'Upload' in df.columns:
        df = df[df['Upload'] > 0]
    if 'Ping' in df.columns:
        df = df[df['Ping'] < 10000]
    
    # Converter para Mbps para análise
    df['Download_Mbps'] = df['Download'] / 1e6
    df['Upload_Mbps'] = df['Upload'] / 1e6
    
    # Extrair dia da semana e hora
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['Hour'] = df['Timestamp'].dt.hour
    df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])
    
    return df


def analyze_data(df: pd.DataFrame) -> dict:
    """Gera estatísticas e análises principais."""
    stats = {}
    
    # Estatísticas gerais
    stats['total_records'] = len(df)
    stats['tools'] = df['Tool'].unique().tolist()
    stats['period'] = f"{df['Timestamp'].min()} to {df['Timestamp'].max()}"
    
    if 'Download_Mbps' in df.columns:
        stats['download_stats'] = df['Download_Mbps'].describe().to_dict()
        stats['upload_stats'] = df['Upload_Mbps'].describe().to_dict()
    
    if 'Ping' in df.columns:
        stats['ping_stats'] = df['Ping'].describe().to_dict()
    
    # Análise por dia da semana
    if 'DayOfWeek' in df.columns:
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        stats['weekday_avg_download'] = df.groupby('DayOfWeek')['Download_Mbps'].mean().reindex(weekday_order).to_dict()
    
    # Análise por hora
    if 'Hour' in df.columns:
        stats['hourly_avg_download'] = df.groupby('Hour')['Download_Mbps'].mean().to_dict()
    
    # Detecção de throttling (diferença entre dias úteis e fins de semana)
    if 'IsWeekend' in df.columns:
        weekday_avg = df[~df['IsWeekend']]['Download_Mbps'].mean()
        weekend_avg = df[df['IsWeekend']]['Download_Mbps'].mean()
        if weekday_avg > 0:
            diff_pct = ((weekday_avg - weekend_avg) / weekday_avg) * 100
            stats['throttling_diff_pct'] = diff_pct
            stats['throttling_detected'] = diff_pct > 10
        else:
            stats['throttling_diff_pct'] = 0
            stats['throttling_detected'] = False
    
    return stats


def generate_summary(stats: dict) -> str:
    """Gera um resumo em texto das análises."""
    lines = []
    lines.append("=" * 70)
    lines.append("RESUMO DA ANÁLISE")
    lines.append("=" * 70)
    
    lines.append(f"Período: {stats.get('period', 'N/A')}")
    lines.append(f"Total de registros válidos: {stats.get('total_records', 0)}")
    lines.append(f"Ferramentas: {', '.join(stats.get('tools', []))}")
    
    if 'download_stats' in stats:
        lines.append("\n--- Download (Mbps) ---")
        for k, v in stats['download_stats'].items():
            lines.append(f"  {k}: {v:.2f}")
    
    if 'upload_stats' in stats:
        lines.append("\n--- Upload (Mbps) ---")
        for k, v in stats['upload_stats'].items():
            lines.append(f"  {k}: {v:.2f}")
    
    if 'ping_stats' in stats:
        lines.append("\n--- Ping (ms) ---")
        for k, v in stats['ping_stats'].items():
            lines.append(f"  {k}: {v:.2f}")
    
    if 'weekday_avg_download' in stats:
        lines.append("\n--- Média Download por Dia da Semana (Mbps) ---")
        for day, val in stats['weekday_avg_download'].items():
            lines.append(f"  {day}: {val:.2f}")
    
    if 'hourly_avg_download' in stats:
        lines.append("\n--- Média Download por Hora (Mbps) ---")
        for hour, val in stats['hourly_avg_download'].items():
            lines.append(f"  {hour:02d}:00 - {val:.2f}")
    
    if 'throttling_detected' in stats:
        lines.append("\n--- Detecção de Throttling ---")
        lines.append(f"  Diferença entre dias úteis e fins de semana: {stats['throttling_diff_pct']:.2f}%")
        lines.append(f"  Throttling detectado: {'SIM' if stats['throttling_detected'] else 'NÃO'}")
    
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    # Determinar diretório de logs
    log_dir = sys.argv[1] if len(sys.argv) > 1 else "/app/data/logs"
    if not os.path.isdir(log_dir):
        log_dir = os.path.join(os.getcwd(), "data", "logs")
    
    print(f"Carregando dados de: {log_dir}")
    df_raw = load_data(log_dir)
    print(f"Dados brutos carregados: {len(df_raw)} registros")
    
    print("\nLimpando e normalizando dados...")
    df_clean = clean_and_normalize(df_raw)
    print(f"Dados após limpeza: {len(df_clean)} registros")
    
    print("\nExecutando análise...")
    stats = analyze_data(df_clean)
    
    print("\n" + generate_summary(stats))
    
    # Salvar dados limpos
    output_path = os.path.join(log_dir, "clean_normalized_data.csv")
    df_clean.to_csv(output_path, index=False)
    print(f"\nDados limpos salvos em: {output_path}")


if __name__ == "__main__":
    main()