"""Carregamento e cache dos dados a partir dos CSVs."""

import os
import glob
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, timezone


@st.cache_data(ttl=300)
def load_data(log_dir: str, max_days: int = 7) -> pd.DataFrame:
    """
    Carrega apenas os dados dos últimos N dias para evitar lentidão.
    
    Args:
        log_dir: Caminho do diretório onde estão os arquivos *_speed_logs.csv.
        max_days: Número máximo de dias para carregar (padrão: 7 dias).
        
    Returns:
        DataFrame com todos os dados, com coluna 'Tool' adicionada.
    """
    all_files = glob.glob(os.path.join(log_dir, '*_speed_logs.csv'))
    dfs = []
    
    # Data limite para filtrar (timezone-aware para comparar com Timestamp UTC)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_days)
    
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
        
        # FILTRO: manter apenas dados dos últimos max_days
        df = df[df['Timestamp'] >= cutoff]
        
        if 'Server Lat' not in df.columns:
            df['Server Lat'] = 0.0
        if 'Server Lon' not in df.columns:
            df['Server Lon'] = 0.0
        dfs.append(df)
    
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)