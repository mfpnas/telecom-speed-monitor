"""Cálculos estatísticos e processamento de dados para o relatório."""

import pandas as pd
from typing import Dict, Tuple, List


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra dados válidos das ferramentas speedtest-cli e librespeed.

    Args:
        df: DataFrame bruto com colunas 'Tool', 'Download', 'Upload', 'Ping'.

    Returns:
        DataFrame limpo com registros válidos (Download>0, Upload>0, Ping<10000).
    """
    allowed_tools = ['speedtest-cli', 'librespeed']
    df_filtered = df[df['Tool'].isin(allowed_tools)].copy()
    mask = (df_filtered['Download'] > 0) & (df_filtered['Upload'] > 0) & (df_filtered['Ping'] < 10000)
    return df_filtered[mask]


def compute_success_rates(df: pd.DataFrame) -> List[List[str]]:
    """Calcula a taxa de sucesso por ferramenta.

    Args:
        df: DataFrame com colunas 'Tool', 'Download', 'Upload', 'Ping'.

    Returns:
        Lista de listas no formato:
        [['Ferramenta', 'Total Testes', 'Válidos', 'Taxa de Sucesso'],
         ['speedtest-cli', '100', '90', '90.0%'], ...]
    """
    def is_valid_general(row):
        if row['Tool'] == 'fast':
            return row['Download'] > 0
        else:
            return (row['Download'] > 0) & (row['Upload'] > 0) & (row['Ping'] < 10000)

    result = [["Ferramenta", "Total Testes", "Válidos", "Taxa de Sucesso"]]
    for tool in df['Tool'].unique():
        tool_df = df[df['Tool'] == tool]
        total = len(tool_df)
        valid = len(tool_df[tool_df.apply(is_valid_general, axis=1)])
        rate = (valid / total * 100) if total > 0 else 0
        result.append([tool, str(total), str(valid), f"{rate:.1f}%"])
    return result


def compute_statistics(clean_df: pd.DataFrame, plan_download: float = 500,
                       plan_upload: float = 250) -> Dict:
    """Calcula todas as métricas estatísticas necessárias para o relatório.

    Args:
        clean_df: DataFrame com dados válidos (já filtrado).
        plan_download: Velocidade de download contratada (Mbps).
        plan_upload: Velocidade de upload contratada (Mbps).

    Returns:
        Dicionário com as seguintes chaves:
            - combined_desc: DataFrame com estatísticas descritivas.
            - weekday_median: Series com medianas por dia da semana.
            - weekend_stats: Series com medianas para weekday e weekend.
            - pct_stats: DataFrame com percentuais por período.
            - throttling: dicionário com 'detected' (bool), 'percent' (float).
            - overall_median_dl: mediana geral de download.
            - overall_median_ul: mediana geral de upload.
            - interruptions: número de interrupções (Download ou Upload = 0).
    """
    # Preparação básica
    clean_df = clean_df.copy()
    clean_df['Download_Mbps'] = clean_df['Download'] / 1e6
    clean_df['Upload_Mbps'] = clean_df['Upload'] / 1e6
    clean_df['DayOfWeek'] = clean_df['Timestamp'].dt.day_name()
    clean_df['IsWeekend'] = clean_df['DayOfWeek'].isin(['Saturday', 'Sunday'])

    # Estatísticas descritivas
    combined_desc = clean_df[['Download_Mbps', 'Upload_Mbps', 'Ping']].describe()

    # Dia da semana
    weekday_median = clean_df.groupby('DayOfWeek')['Download_Mbps'].median()

    # Weekend vs weekday
    weekend_stats = clean_df.groupby('IsWeekend')['Download_Mbps'].median()

    # Percentuais por período
    pct_stats = clean_df.groupby('IsWeekend')[['Download_Mbps', 'Upload_Mbps']].median()
    pct_stats = (pct_stats / [plan_download, plan_upload]) * 100

    # Throttling
    throttling = {'detected': False, 'percent': 0}
    if len(weekend_stats) == 2:
        wk_med = weekend_stats[False]
        we_med = weekend_stats[True]
        if wk_med > 0:
            diff = ((wk_med - we_med) / wk_med) * 100
            if diff > 5:
                throttling['detected'] = True
                throttling['percent'] = diff

    # Medianas gerais
    overall_median_dl = combined_desc.loc['50%', 'Download_Mbps'] if '50%' in combined_desc.index else 0
    overall_median_ul = combined_desc.loc['50%', 'Upload_Mbps'] if '50%' in combined_desc.index else 0

    # Interrupções
    interruptions = len(clean_df[clean_df['Download'] == 0]) + len(clean_df[clean_df['Upload'] == 0])

    return {
        'combined_desc': combined_desc,
        'weekday_median': weekday_median,
        'weekend_stats': weekend_stats,
        'pct_stats': pct_stats,
        'throttling': throttling,
        'overall_median_dl': overall_median_dl,
        'overall_median_ul': overall_median_ul,
        'interruptions': interruptions
    }