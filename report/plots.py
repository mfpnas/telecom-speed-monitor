# report/plots.py
"""Geração de gráficos para o relatório."""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from datetime import datetime
import numpy as np

# Configuração de estilo para os gráficos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def generate_comparison_plots(df_speed: pd.DataFrame, df_librespeed: pd.DataFrame, output_dir: str) -> list:
    """Gera gráficos comparativos entre speedtest-cli e LibreSpeed."""
    images = []
    
    # Garantir que temos dados
    if df_speed.empty and df_librespeed.empty:
        return images
    
    # Combinar dados para gráficos comparativos
    df_combined = pd.concat([df_speed, df_librespeed], ignore_index=True)
    
    # 1. Gráfico de distribuição de Download
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    if not df_speed.empty:
        sns.kdeplot(data=df_speed, x='Download_Mbps', label='speedtest-cli', ax=ax1, fill=True, alpha=0.5)
    if not df_librespeed.empty:
        sns.kdeplot(data=df_librespeed, x='Download_Mbps', label='librespeed', ax=ax1, fill=True, alpha=0.5)
    ax1.set_title('Distribuição de Download por Ferramenta', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Download (Mbps)')
    ax1.set_ylabel('Densidade')
    ax1.legend()
    img1 = os.path.join(output_dir, 'download_distribution.png')
    plt.savefig(img1, dpi=150, bbox_inches='tight')
    plt.close(fig1)
    images.append(img1)
    
    # 2. Gráfico de distribuição de Upload
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    if not df_speed.empty:
        sns.kdeplot(data=df_speed, x='Upload_Mbps', label='speedtest-cli', ax=ax2, fill=True, alpha=0.5)
    if not df_librespeed.empty:
        sns.kdeplot(data=df_librespeed, x='Upload_Mbps', label='librespeed', ax=ax2, fill=True, alpha=0.5)
    ax2.set_title('Distribuição de Upload por Ferramenta', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Upload (Mbps)')
    ax2.set_ylabel('Densidade')
    ax2.legend()
    img2 = os.path.join(output_dir, 'upload_distribution.png')
    plt.savefig(img2, dpi=150, bbox_inches='tight')
    plt.close(fig2)
    images.append(img2)
    
    # 3. Boxplot de Download por ferramenta
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    data_to_plot = []
    labels = []
    if not df_speed.empty:
        data_to_plot.append(df_speed['Download_Mbps'].dropna())
        labels.append('speedtest-cli')
    if not df_librespeed.empty:
        data_to_plot.append(df_librespeed['Download_Mbps'].dropna())
        labels.append('librespeed')
    if data_to_plot:
        bp = ax3.boxplot(data_to_plot, labels=labels, patch_artist=True)
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
            patch.set_alpha(0.7)
        ax3.set_title('Boxplot de Download por Ferramenta', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Download (Mbps)')
        ax3.grid(True, alpha=0.3)
    img3 = os.path.join(output_dir, 'download_boxplot.png')
    plt.savefig(img3, dpi=150, bbox_inches='tight')
    plt.close(fig3)
    images.append(img3)
    
    # 4. Gráfico de séries temporais (Download)
    fig4, ax4 = plt.subplots(figsize=(14, 6))
    if not df_speed.empty:
        df_speed_sorted = df_speed.sort_values('Timestamp')
        ax4.plot(df_speed_sorted['Timestamp'], df_speed_sorted['Download_Mbps'], 
                label='speedtest-cli', alpha=0.7, linewidth=1)
    if not df_librespeed.empty:
        df_librespeed_sorted = df_librespeed.sort_values('Timestamp')
        ax4.plot(df_librespeed_sorted['Timestamp'], df_librespeed_sorted['Download_Mbps'], 
                label='librespeed', alpha=0.7, linewidth=1)
    ax4.set_title('Evolução do Download ao Longo do Tempo', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Data/Hora')
    ax4.set_ylabel('Download (Mbps)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    img4 = os.path.join(output_dir, 'time_series_download.png')
    plt.savefig(img4, dpi=150, bbox_inches='tight')
    plt.close(fig4)
    images.append(img4)
    
    # 5. Gráfico por dia da semana
    fig5, ax5 = plt.subplots(figsize=(12, 6))
    
    # Preparar dados por dia da semana
    df_combined['DayOfWeek'] = df_combined['Timestamp'].dt.day_name()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Calcular medianas por dia
    weekday_medians = df_combined.groupby('DayOfWeek')['Download_Mbps'].median().reindex(weekday_order)
    
    # Barras com cores diferentes para dias úteis e fins de semana
    colors = ['#2E86AB' if day not in ['Saturday', 'Sunday'] else '#A23B72' for day in weekday_order]
    bars = ax5.bar(weekday_order, weekday_medians.values, color=colors, alpha=0.7)
    ax5.set_title('Mediana de Download por Dia da Semana', fontsize=14, fontweight='bold')
    ax5.set_xlabel('Dia da Semana')
    ax5.set_ylabel('Download Mediano (Mbps)')
    ax5.axhline(y=500, color='red', linestyle='--', label='Contratado (500 Mbps)')
    ax5.axhline(y=400, color='orange', linestyle='--', label='Mínimo Anatel (400 Mbps)')
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    img5 = os.path.join(output_dir, 'weekday_analysis.png')
    plt.savefig(img5, dpi=150, bbox_inches='tight')
    plt.close(fig5)
    images.append(img5)
    
    # 6. Comparação Dias Úteis vs Fins de Semana
    fig6, ax6 = plt.subplots(figsize=(10, 6))
    
    # Criar coluna de tipo de dia
    df_combined['IsWeekend'] = df_combined['DayOfWeek'].isin(['Saturday', 'Sunday'])
    df_combined['Period'] = df_combined['IsWeekend'].map({True: 'Fim de Semana', False: 'Dia Útil'})
    
    # Boxplot comparativo
    data_to_plot = []
    labels = []
    if not df_combined[df_combined['IsWeekend'] == False].empty:
        data_to_plot.append(df_combined[df_combined['IsWeekend'] == False]['Download_Mbps'].dropna())
        labels.append('Dias Úteis')
    if not df_combined[df_combined['IsWeekend'] == True].empty:
        data_to_plot.append(df_combined[df_combined['IsWeekend'] == True]['Download_Mbps'].dropna())
        labels.append('Fins de Semana')
    
    if data_to_plot:
        bp = ax6.boxplot(data_to_plot, labels=labels, patch_artist=True)
        colors_box = ['#2E86AB', '#A23B72']
        for patch, color in zip(bp['boxes'], colors_box):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax6.set_title('Comparação: Dias Úteis vs Fins de Semana', fontsize=14, fontweight='bold')
        ax6.set_ylabel('Download (Mbps)')
        ax6.grid(True, alpha=0.3)
    
    img6 = os.path.join(output_dir, 'weekend_comparison.png')
    plt.savefig(img6, dpi=150, bbox_inches='tight')
    plt.close(fig6)
    images.append(img6)
    
    # 7. Gráfico de calor por hora e dia da semana (Análise Inteligente)
    fig7, ax7 = plt.subplots(figsize=(14, 8))
    
    # Preparar dados para heatmap
    df_combined['Hour'] = df_combined['Timestamp'].dt.hour
    df_combined['DayOfWeek'] = df_combined['Timestamp'].dt.day_name()
    
    # Calcular mediana por dia e hora
    heatmap_data = df_combined.groupby(['DayOfWeek', 'Hour'])['Download_Mbps'].median().unstack()
    
    # Reordenar dias da semana
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(day_order)
    
    if not heatmap_data.empty:
        # Criar heatmap
        sns.heatmap(heatmap_data, ax=ax7, cmap='RdYlGn', center=250, 
                   cbar_kws={'label': 'Download Mediano (Mbps)'})
        ax7.set_title('Mediana de Download por Dia e Hora', fontsize=14, fontweight='bold')
        ax7.set_xlabel('Hora do Dia')
        ax7.set_ylabel('Dia da Semana')
        
        # Destacar células com valores abaixo de 200 Mbps (40% do contratado)
        # Isso é feito através da coloração do heatmap
    
    img7 = os.path.join(output_dir, 'heatmap_hour_day.png')
    plt.savefig(img7, dpi=150, bbox_inches='tight')
    plt.close(fig7)
    images.append(img7)
    
    return images

def generate_smart_analysis(df: pd.DataFrame, output_dir: str) -> dict:
    """Gera análise inteligente de padrões de velocidade."""
    
    if df.empty:
        return {
            'problem_hours': [],
            'throttling_hours': [],
            'worst_day': '',
            'worst_day_avg': 0
        }
    
    # Criar colunas auxiliares
    df = df.copy()
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['Hour'] = df['Timestamp'].dt.hour
    df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])
    df['Download_Mbps'] = df['Download'] / 1_000_000
    
    # 1. Identificar horários com velocidade abaixo de 50% do contratado (250 Mbps)
    problem_hours = []
    threshold_50 = 250  # 50% de 500 Mbps
    
    # Agrupar por dia da semana e hora
    hourly_median = df.groupby(['DayOfWeek', 'Hour'])['Download_Mbps'].median()
    
    # Mapear dias da semana em português
    day_map = {
        'Monday': 'Segunda',
        'Tuesday': 'Terça',
        'Wednesday': 'Quarta',
        'Thursday': 'Quinta',
        'Friday': 'Sexta',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    
    for (day, hour), value in hourly_median.items():
        if value < threshold_50:
            # Verificar se há dados suficientes para este horário (pelo menos 3 medições)
            count = len(df[(df['DayOfWeek'] == day) & (df['Hour'] == hour)])
            if count >= 3:
                problem_hours.append({
                    'day': day_map.get(day, day),
                    'hour': hour,
                    'speed': value,
                    'pct': (value / 500) * 100,
                    'count': count
                })
    
    # Ordenar por velocidade (menor primeiro)
    problem_hours.sort(key=lambda x: x['speed'])
    
    # 2. Identificar possíveis horários de throttling (diferença > 20% entre dias úteis e fins de semana)
    throttling_hours = []
    
    # Calcular mediana por hora para dias úteis e fins de semana
    weekday_hourly = df[~df['IsWeekend']].groupby('Hour')['Download_Mbps'].median()
    weekend_hourly = df[df['IsWeekend']].groupby('Hour')['Download_Mbps'].median()
    
    for hour in range(24):
        if hour in weekday_hourly and hour in weekend_hourly:
            weekday_val = weekday_hourly[hour]
            weekend_val = weekend_hourly[hour]
            
            if weekday_val > 0 and weekend_val < weekday_val:
                diff_pct = ((weekday_val - weekend_val) / weekday_val) * 100
                if diff_pct > 20:  # Diferença maior que 20%
                    throttling_hours.append({
                        'hour': hour,
                        'weekday_speed': weekday_val,
                        'weekend_speed': weekend_val,
                        'diff_pct': diff_pct
                    })
    
    throttling_hours.sort(key=lambda x: x['diff_pct'], reverse=True)
    
    # 3. Identificar o pior dia da semana
    daily_avg = df.groupby('DayOfWeek')['Download_Mbps'].median()
    if not daily_avg.empty:
        worst_day_eng = daily_avg.idxmin()
        worst_day = day_map.get(worst_day_eng, worst_day_eng)
        worst_avg = daily_avg.min()
    else:
        worst_day = ''
        worst_avg = 0
    
    return {
        'problem_hours': problem_hours,
        'throttling_hours': throttling_hours,
        'worst_day': worst_day,
        'worst_day_avg': worst_avg
    }