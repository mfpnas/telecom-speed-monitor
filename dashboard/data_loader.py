"""Carregamento e cache dos dados."""

import os
import glob
import pandas as pd
import streamlit as st


@st.cache_data(ttl=300)
def load_data(log_dir: str) -> pd.DataFrame:
    """Carrega todos os CSVs do diretório e os concatena em um único DataFrame.

    Args:
        log_dir: Diretório onde estão os arquivos *_speed_logs.csv.

    Returns:
        DataFrame com todos os dados, com coluna 'Tool' adicionada.
    """
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
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        elif 'timestamp' in df.columns:
            df.rename(columns={'timestamp': 'Timestamp'}, inplace=True)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        else:
            mtime = os.path.getmtime(f)
            df['Timestamp'] = pd.to_datetime(mtime, unit='s', utc=True)
        if 'Server Lat' not in df.columns:
            df['Server Lat'] = 0.0
        if 'Server Lon' not in df.columns:
            df['Server Lon'] = 0.0
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)