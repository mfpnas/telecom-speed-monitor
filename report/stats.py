# report/stats.py
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from typing import Dict, List

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    allowed_tools = ['speedtest-cli', 'librespeed']
    df_filtered = df[df['Tool'].isin(allowed_tools)].copy()
    mask = (df_filtered['Download'] > 0) & (df_filtered['Upload'] > 0) & (df_filtered['Ping'] < 10000)
    return df_filtered[mask]

def compute_success_rates(df: pd.DataFrame) -> List[List[str]]:
    def is_valid_general(row):
        if row['Tool'] == 'fast':
            return row['Download'] > 0
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
    clean_df = clean_df.copy()
    clean_df['Download_Mbps'] = clean_df['Download'] / 1e6
    clean_df['Upload_Mbps'] = clean_df['Upload'] / 1e6
    clean_df['DayOfWeek'] = clean_df['Timestamp'].dt.day_name()
    clean_df['IsWeekend'] = clean_df['DayOfWeek'].isin(['Saturday', 'Sunday'])

    combined_desc = clean_df[['Download_Mbps', 'Upload_Mbps', 'Ping']].describe()
    weekday_median = clean_df.groupby('DayOfWeek')['Download_Mbps'].median()
    weekend_stats = clean_df.groupby('IsWeekend')['Download_Mbps'].median()

    pct_stats = clean_df.groupby('IsWeekend')[['Download_Mbps', 'Upload_Mbps']].median()
    pct_stats = (pct_stats / [plan_download, plan_upload]) * 100

    throttling = {'detected': False, 'percent': 0, 'p_value': 1.0,
                  'weekday_median': 0, 'weekend_median': 0}

    if len(weekend_stats) == 2:
        weekday_data = clean_df[~clean_df['IsWeekend']]['Download_Mbps'].dropna()
        weekend_data = clean_df[clean_df['IsWeekend']]['Download_Mbps'].dropna()
        if len(weekday_data) >= 10 and len(weekend_data) >= 10:
            u_stat, p_value = scipy_stats.mannwhitneyu(weekday_data, weekend_data, alternative='two-sided')
            wk_med = weekday_data.median()
            we_med = weekend_data.median()
            if wk_med > 0:
                percent_diff = ((wk_med - we_med) / wk_med) * 100
            else:
                percent_diff = 0
            if percent_diff > 10 and p_value < 0.05:
                throttling['detected'] = True
                throttling['percent'] = percent_diff
                throttling['p_value'] = p_value
                throttling['weekday_median'] = wk_med
                throttling['weekend_median'] = we_med

    overall_median_dl = combined_desc.loc['50%', 'Download_Mbps'] if '50%' in combined_desc.index else 0
    overall_median_ul = combined_desc.loc['50%', 'Upload_Mbps'] if '50%' in combined_desc.index else 0

    interruptions = ((clean_df['Download'] == 0) | (clean_df['Upload'] == 0)).sum()

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