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
            _, p_value = scipy_stats.mannwhitneyu(weekday_data, weekend_data, alternative='two-sided')
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

def intelligent_analysis(clean_df: pd.DataFrame, plan_download: float = 500,
                         plan_upload: float = 250) -> Dict:
    """
    Análise inteligente por dia da semana e faixa horária.
    Identifica dias/horários críticos e possível throttling.
    """
    clean_df = clean_df.copy()
    clean_df['Download_Mbps'] = clean_df['Download'] / 1e6
    clean_df['Upload_Mbps'] = clean_df['Upload'] / 1e6
    clean_df['DayOfWeek'] = clean_df['Timestamp'].dt.day_name()
    clean_df['Hour'] = clean_df['Timestamp'].dt.hour

    # Definir faixas horárias
    def get_period(hour):
        if 0 <= hour < 6:
            return 'Madrugada (00h-06h)'
        elif 6 <= hour < 12:
            return 'Manhã (06h-12h)'
        elif 12 <= hour < 18:
            return 'Tarde (12h-18h)'
        else:
            return 'Noite (18h-24h)'

    clean_df['Period'] = clean_df['Hour'].apply(get_period)

    # Análise por dia da semana
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    day_analysis = {}
    for day in days_order:
        day_data = clean_df[clean_df['DayOfWeek'] == day]['Download_Mbps'].dropna()
        if not day_data.empty:
            med = day_data.median()
            pct = (med / plan_download) * 100 if plan_download > 0 else 0
            day_analysis[day] = {
                'median': med,
                'pct': pct,
                'critical': pct < 50,
                'label': dias_pt[days_order.index(day)]
            }

    # Análise por faixa horária
    periods_order = ['Madrugada (00h-06h)', 'Manhã (06h-12h)', 'Tarde (12h-18h)', 'Noite (18h-24h)']
    period_analysis = {}
    for period in periods_order:
        period_data = clean_df[clean_df['Period'] == period]['Download_Mbps'].dropna()
        if not period_data.empty:
            med = period_data.median()
            pct = (med / plan_download) * 100 if plan_download > 0 else 0
            period_analysis[period] = {
                'median': med,
                'pct': pct,
                'critical': pct < 50,
                'count': len(period_data)
            }

    # Análise por dia + período (para detecção de throttling)
    combined = {}
    for day in days_order:
        for period in periods_order:
            subset = clean_df[(clean_df['DayOfWeek'] == day) & (clean_df['Period'] == period)]
            if not subset.empty:
                med = subset['Download_Mbps'].median()
                pct = (med / plan_download) * 100 if plan_download > 0 else 0
                combined[f"{day}_{period}"] = {
                    'median': med,
                    'pct': pct,
                    'count': len(subset)
                }

    # Identificar padrões problemáticos
    critical_days = [day_analysis[d]['label'] for d in day_analysis if day_analysis[d]['critical']]
    critical_periods = [p for p in period_analysis if period_analysis[p]['critical']]

    # Verificar throttling por faixa horária (dias úteis vs fins de semana)
    throttle_periods = []
    for period in periods_order:
        weekday_data = clean_df[(clean_df['Period'] == period) & (~clean_df['IsWeekend'])]['Download_Mbps'].dropna()
        weekend_data = clean_df[(clean_df['Period'] == period) & (clean_df['IsWeekend'])]['Download_Mbps'].dropna()
        if len(weekday_data) >= 5 and len(weekend_data) >= 5:
            wk_med = weekday_data.median()
            we_med = weekend_data.median()
            if wk_med > 0:
                diff = ((wk_med - we_med) / wk_med) * 100
                if diff > 20:
                    throttle_periods.append({
                        'period': period,
                        'weekday_median': wk_med,
                        'weekend_median': we_med,
                        'percent_diff': diff
                    })

    # Gerar resumo
    summary = []
    if critical_days:
        summary.append(f"Dias críticos: {', '.join(critical_days)} (mediana < 50% da contratada).")
    if critical_periods:
        summary.append(f"Horários críticos: {', '.join(critical_periods)} (mediana < 50% da contratada).")
    if throttle_periods:
        for tp in throttle_periods:
            summary.append(f"Possível throttling no período {tp['period']}: diferença de {tp['percent_diff']:.1f}% entre dias úteis e fins de semana.")

    if not summary:
        summary.append("Nenhum padrão crítico ou de throttling identificado nas faixas analisadas.")

    return {
        'day_analysis': day_analysis,
        'period_analysis': period_analysis,
        'combined': combined,
        'critical_days': critical_days,
        'critical_periods': critical_periods,
        'throttle_periods': throttle_periods,
        'summary': summary
    }