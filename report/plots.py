"""Geração de gráficos comparativos para o relatório."""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Tuple


def generate_comparison_plots(df_speed: pd.DataFrame, df_librespeed: pd.DataFrame,
                              output_dir: str) -> List[str]:
    """Gera gráficos comparativos entre speedtest-cli e LibreSpeed.

    Args:
        df_speed: DataFrame da ferramenta speedtest-cli (já com colunas convertidas).
        df_librespeed: DataFrame da ferramenta librespeed.
        output_dir: Diretório onde salvar os arquivos PNG.

    Returns:
        Lista com os nomes dos arquivos de imagem gerados.
    """
    # Preparar dados
    df_speed = df_speed.copy()
    df_librespeed = df_librespeed.copy()
    df_speed['Tool'] = 'speedtest-cli'
    df_librespeed['Tool'] = 'librespeed'
    combined = pd.concat([df_speed, df_librespeed], ignore_index=True)

    images = []

    # 1. Time Series: Download e Upload (sobrepostos)
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    for tool, df in [('speedtest-cli', df_speed), ('librespeed', df_librespeed)]:
        axes[0].plot(df['Timestamp'], df['Download_Mbps'], alpha=0.5, label=tool)
        axes[1].plot(df['Timestamp'], df['Upload_Mbps'], alpha=0.5, label=tool)
    axes[0].set_title('Evolução do Download')
    axes[0].set_ylabel('Mbps')
    axes[0].legend()
    axes[1].set_title('Evolução do Upload')
    axes[1].set_ylabel('Mbps')
    axes[1].legend()
    plt.tight_layout()
    fname = 'time_series_comparison.png'
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()
    images.append(fname)

    # 2. Distribuição: Download e Upload (lado a lado)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for tool, df in [('speedtest-cli', df_speed), ('librespeed', df_librespeed)]:
        sns.histplot(df['Download_Mbps'], kde=True, label=tool, ax=axes[0], alpha=0.5)
        sns.histplot(df['Upload_Mbps'], kde=True, label=tool, ax=axes[1], alpha=0.5)
    axes[0].set_title('Distribuição do Download')
    axes[0].set_xlabel('Mbps')
    axes[0].legend()
    axes[1].set_title('Distribuição do Upload')
    axes[1].set_xlabel('Mbps')
    axes[1].legend()
    plt.tight_layout()
    fname = 'distribuicao_comparison.png'
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()
    images.append(fname)

    # 3. Boxplot por ferramenta (download e upload)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    sns.boxplot(data=combined, x='Tool', y='Download_Mbps', ax=axes[0])
    axes[0].set_title('Download por Ferramenta')
    sns.boxplot(data=combined, x='Tool', y='Upload_Mbps', ax=axes[1])
    axes[1].set_title('Upload por Ferramenta')
    plt.tight_layout()
    fname = 'boxplot_comparison.png'
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()
    images.append(fname)

    # 4. Scatter: Ping vs Download (comparativo)
    fig, ax = plt.subplots(figsize=(10, 6))
    for tool, df in [('speedtest-cli', df_speed), ('librespeed', df_librespeed)]:
        ax.scatter(df['Ping'], df['Download_Mbps'], alpha=0.5, label=tool, s=10)
    ax.set_xlabel('Ping (ms)')
    ax.set_ylabel('Download (Mbps)')
    ax.set_title('Relação Ping vs Download')
    ax.legend()
    plt.tight_layout()
    fname = 'scatter_comparison.png'
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()
    images.append(fname)

    # 5. Média horária (comparativa)
    fig, ax = plt.subplots(figsize=(12, 6))
    for tool, df in [('speedtest-cli', df_speed), ('librespeed', df_librespeed)]:
        df['Hour'] = df['Timestamp'].dt.hour
        hourly = df.groupby('Hour')['Download_Mbps'].mean()
        ax.plot(hourly.index, hourly.values, marker='o', label=tool)
    ax.set_xlabel('Hora do Dia')
    ax.set_ylabel('Download Médio (Mbps)')
    ax.set_title('Média Horária do Download')
    ax.legend()
    plt.tight_layout()
    fname = 'hourly_comparison.png'
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()
    images.append(fname)

    # 6. Média por dia da semana (comparativa)
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    fig, ax = plt.subplots(figsize=(12, 6))
    for tool, df in [('speedtest-cli', df_speed), ('librespeed', df_librespeed)]:
        df['DayOfWeek'] = df['Timestamp'].dt.day_name()
        weekday_avg = df.groupby('DayOfWeek')['Download_Mbps'].mean().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )
        weekday_avg.index = dias_pt
        ax.plot(weekday_avg.index, weekday_avg.values, marker='s', label=tool)
    ax.set_xlabel('Dia da Semana')
    ax.set_ylabel('Download Médio (Mbps)')
    ax.set_title('Média por Dia da Semana')
    ax.legend()
    plt.tight_layout()
    fname = 'weekday_comparison.png'
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()
    images.append(fname)

    # 7. Gráfico de medianas (barras)
    med_speed_dl = df_speed['Download_Mbps'].median()
    med_speed_ul = df_speed['Upload_Mbps'].median()
    med_libre_dl = df_librespeed['Download_Mbps'].median()
    med_libre_ul = df_librespeed['Upload_Mbps'].median()

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(2)
    width = 0.35
    ax.bar(x - width/2, [med_speed_dl, med_speed_ul], width, label='speedtest-cli')
    ax.bar(x + width/2, [med_libre_dl, med_libre_ul], width, label='librespeed')
    ax.set_xticks(x)
    ax.set_xticklabels(['Download', 'Upload'])
    ax.set_ylabel('Mediana (Mbps)')
    ax.set_title('Mediana das Velocidades por Ferramenta')
    ax.legend()
    plt.tight_layout()
    fname = 'medianas.png'
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()
    images.append(fname)

    return images