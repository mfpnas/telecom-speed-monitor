#!/usr/bin/env python3
"""
Script de Limpeza, Normalização e Análise de Dados do Telecom Speed Monitor.

Este script:
1. Carrega todos os CSVs do diretório de logs.
2. Normaliza as unidades (converte valores do librespeed de Mbps para bps se necessário).
3. Remove registros inválidos (Download/Upload = 0, Ping > 10000 ms).
4. Gera estatísticas resumidas e gráficos de verificação.
5. Salva os dados limpos em um novo diretório.

Uso manual:
    python3 scripts/clean_normalize_dataanalysis.py
    python3 scripts/clean_normalize_dataanalysis.py --log_dir /path/to/logs
"""

import os
import glob
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

# Configuração
DEFAULT_LOG_DIR = "./data/logs"
CLEAN_DIR = "./data/clean_logs"  # Diretório onde os dados limpos serão salvos
MAX_PING_MS = 10000  # Limite de ping aceitável
MIN_SPEED_BPS = 1000  # Velocidade mínima para considerar válida (1 kbps)


def detect_unit(value: float, tool: str) -> str:
    """
    Detecta se o valor de velocidade está em bps ou Mbps.
    
    Args:
        value: Valor de velocidade.
        tool: Nome da ferramenta que gerou o dado.
        
    Returns:
        'bps' se o valor parece estar em bits por segundo,
        'mbps' se o valor parece estar em megabits por segundo.
    """
    # Para librespeed, valores pequenos (< 100000) provavelmente estão em Mbps
    if tool == 'librespeed' and value < 100000:
        return 'mbps'
    # Para outras ferramentas, valores pequenos podem indicar Mbps ou Kbps
    elif value < 1000:
        return 'mbps'  # Assume Mbps para valores muito pequenos
    else:
        return 'bps'


def normalize_to_bps(value: float, tool: str) -> float:
    """
    Converte qualquer valor para bits por segundo (bps).
    
    Args:
        value: Valor de velocidade.
        tool: Nome da ferramenta que gerou o dado.
        
    Returns:
        Valor em bps.
    """
    if pd.isna(value) or value <= 0:
        return 0
    
    unit = detect_unit(value, tool)
    if unit == 'mbps':
        return float(value * 1e6)  # Mbps -> bps
    elif unit == 'bps':
        return float(value)
    else:
        return float(value)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e normaliza um DataFrame de dados de velocidade.
    
    Args:
        df: DataFrame bruto.
        
    Returns:
        DataFrame limpo e normalizado.
    """
    df = df.copy()
    
    # Converter Timestamp para datetime UTC
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], utc=True)
    
    # Normalizar unidades de Download e Upload
    if 'Download' in df.columns:
        df['Download'] = df.apply(lambda row: normalize_to_bps(row['Download'], row.get('Tool', 'speedtest-cli')), axis=1)
    if 'Upload' in df.columns:
        df['Upload'] = df.apply(lambda row: normalize_to_bps(row['Upload'], row.get('Tool', 'speedtest-cli')), axis=1)
    
    # Remover registros inválidos
    if 'Download' in df.columns and 'Upload' in df.columns:
        df = df[(df['Download'] > MIN_SPEED_BPS) | (df['Upload'] > MIN_SPEED_BPS)]
        df = df[~((df['Download'] == 0) & (df['Upload'] == 0))]
    if 'Ping' in df.columns:
        df = df[df['Ping'] < MAX_PING_MS]
    
    # Converter para Mbps para facilitar análise
    if 'Download' in df.columns:
        df['Download_Mbps'] = df['Download'] / 1e6
    if 'Upload' in df.columns:
        df['Upload_Mbps'] = df['Upload'] / 1e6
    
    # Adicionar colunas derivadas
    if 'Timestamp' in df.columns:
        df['Hour'] = df['Timestamp'].dt.hour
        df['DayOfWeek'] = df['Timestamp'].dt.day_name()
        df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])
        df['Date'] = df['Timestamp'].dt.date
    
    return df


def load_and_clean(log_dir: str) -> pd.DataFrame:
    """
    Carrega todos os CSVs, limpa e concatena.
    
    Args:
        log_dir: Diretório onde estão os CSVs.
        
    Returns:
        DataFrame limpo e consolidado.
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
        df = clean_dataframe(df)
        dfs.append(df)
    
    if not dfs:
        return pd.DataFrame()
    
    return pd.concat(dfs, ignore_index=True)


def generate_summary(df: pd.DataFrame) -> dict:
    """
    Gera um resumo estatístico dos dados limpos.
    
    Args:
        df: DataFrame limpo.
        
    Returns:
        Dicionário com estatísticas.
    """
    summary = {
        'total_records': len(df),
        'tools': df['Tool'].value_counts().to_dict(),
        'date_range': (df['Timestamp'].min(), df['Timestamp'].max()) if not df.empty else None,
        'download_stats': {
            'mean': df['Download_Mbps'].mean() if not df.empty else 0,
            'median': df['Download_Mbps'].median() if not df.empty else 0,
            'min': df['Download_Mbps'].min() if not df.empty else 0,
            'max': df['Download_Mbps'].max() if not df.empty else 0,
        },
        'upload_stats': {
            'mean': df['Upload_Mbps'].mean() if not df.empty else 0,
            'median': df['Upload_Mbps'].median() if not df.empty else 0,
        },
        'ping_stats': {
            'mean': df['Ping'].mean() if not df.empty else 0,
            'median': df['Ping'].median() if not df.empty else 0,
        },
        'interruptions': ((df['Download'] == 0) | (df['Upload'] == 0)).sum() if not df.empty else 0,
        'invalid_records_removed': 0  # Será preenchido manualmente pelo usuário
    }
    
    return summary


def save_clean_data(df: pd.DataFrame, output_dir: str):
    """
    Salva os dados limpos em CSVs separados por ferramenta.
    
    Args:
        df: DataFrame limpo.
        output_dir: Diretório de saída.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for tool in df['Tool'].unique():
        tool_df = df[df['Tool'] == tool]
        output_path = os.path.join(output_dir, f"{tool}_speed_logs_clean.csv")
        tool_df.to_csv(output_path, index=False)
        print(f"  Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Limpeza e normalização de dados do Telecom Speed Monitor')
    parser.add_argument('--log_dir', default=DEFAULT_LOG_DIR, help='Diretório com os CSVs originais')
    parser.add_argument('--output_dir', default=CLEAN_DIR, help='Diretório para salvar os dados limpos')
    parser.add_argument('--analyze', action='store_true', help='Gerar gráficos de análise')
    args = parser.parse_args()

    print("=" * 60)
    print("Telecom Speed Monitor - Limpeza e Normalização de Dados")
    print("=" * 60)
    
    print(f"\n📂 Diretório de logs: {args.log_dir}")
    print(f"💾 Diretório de saída: {args.output_dir}")
    
    # Carregar e limpar dados
    print("\n🔄 Carregando e limpando dados...")
    df = load_and_clean(args.log_dir)
    
    if df.empty:
        print("❌ Nenhum dado válido encontrado.")
        return
    
    print(f"✅ Dados carregados: {len(df)} registros válidos")
    
    # Resumo
    summary = generate_summary(df)
    
    print("\n📊 RESUMO DOS DADOS LIMPOS:")
    print(f"  Total de registros: {summary['total_records']}")
    print(f"  Ferramentas: {summary['tools']}")
    print(f"  Período: {summary['date_range'][0].strftime('%Y-%m-%d %H:%M')} a {summary['date_range'][1].strftime('%Y-%m-%d %H:%M')}")
    print(f"  Download médio: {summary['download_stats']['mean']:.2f} Mbps")
    print(f"  Download mediano: {summary['download_stats']['median']:.2f} Mbps")
    print(f"  Upload médio: {summary['upload_stats']['mean']:.2f} Mbps")
    print(f"  Upload mediano: {summary['upload_stats']['median']:.2f} Mbps")
    print(f"  Ping médio: {summary['ping_stats']['mean']:.2f} ms")
    print(f"  Ping mediano: {summary['ping_stats']['median']:.2f} ms")
    print(f"  Interrupções detectadas: {summary['interruptions']}")
    
    # Salvar dados limpos
    print("\n💾 Salvando dados limpos...")
    save_clean_data(df, args.output_dir)
    
    # Análise opcional
    if args.analyze:
        print("\n📈 Gerando gráficos de análise...")
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Configuração de estilo
            sns.set_style("whitegrid")
            plt.rcParams['figure.figsize'] = (12, 6)
            
            # Criar diretório para gráficos
            plots_dir = os.path.join(args.output_dir, 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            # 1. Distribuição de Download por ferramenta
            plt.figure(figsize=(12, 6))
            sns.histplot(data=df, x='Download_Mbps', hue='Tool', kde=True, alpha=0.6)
            plt.title('Distribuição de Download por Ferramenta')
            plt.xlabel('Download (Mbps)')
            plt.savefig(os.path.join(plots_dir, 'download_distribution.png'), dpi=150, bbox_inches='tight')
            plt.close()
            
            # 2. Boxplot por ferramenta
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=df, x='Tool', y='Download_Mbps')
            plt.title('Download por Ferramenta')
            plt.ylabel('Download (Mbps)')
            plt.savefig(os.path.join(plots_dir, 'download_boxplot.png'), dpi=150, bbox_inches='tight')
            plt.close()
            
            # 3. Série temporal
            plt.figure(figsize=(14, 6))
            for tool in df['Tool'].unique():
                tool_df = df[df['Tool'] == tool]
                plt.plot(tool_df['Timestamp'], tool_df['Download_Mbps'], alpha=0.7, label=tool)
            plt.title('Evolução do Download ao Longo do Tempo')
            plt.ylabel('Download (Mbps)')
            plt.legend()
            plt.savefig(os.path.join(plots_dir, 'time_series_download.png'), dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  Gráficos salvos em: {plots_dir}")
        except ImportError:
            print("  ⚠️ matplotlib não disponível. Instale com: pip install matplotlib seaborn")
    
    print("\n✅ Processo concluído com sucesso!")


if __name__ == "__main__":
    main()