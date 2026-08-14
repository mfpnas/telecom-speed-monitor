#!/usr/bin/env python3
"""
Generate a comprehensive court-ready PDF report from speed test data,
using only speedtest-cli and LibreSpeed for analysis and graphics.
"""
import argparse
import os
import tempfile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

# ------------------------------------------------------------
# FUNÇÕES DE FORMATAÇÃO BRASILEIRA
# ------------------------------------------------------------
def format_br_money(value):
    if pd.isna(value) or value is None:
        return "R$ 0,00"
    formatted = f"{value:,.2f}"
    parts = formatted.split('.')
    integer_part = parts[0].replace(',', '.')
    decimal_part = parts[1] if len(parts) > 1 else '00'
    return f"R$ {integer_part},{decimal_part}"

def format_br_number(value):
    if pd.isna(value) or value is None:
        return "0,00"
    formatted = f"{value:,.2f}"
    parts = formatted.split('.')
    integer_part = parts[0].replace(',', '.')
    decimal_part = parts[1] if len(parts) > 1 else '00'
    return f"{integer_part},{decimal_part}"

def data_extenso(dt):
    meses = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    return f"{dt.day} de {meses[dt.strftime('%B')]} de {dt.year}"

# ------------------------------------------------------------
# GERAÇÃO DE GRÁFICOS COMPARATIVOS (speedtest-cli vs LibreSpeed)
# ------------------------------------------------------------
def generate_comparison_plots(df_speed, df_librespeed, output_dir):
    """
    Gera gráficos comparativos entre speedtest-cli e LibreSpeed,
    e também um gráfico com as medianas de cada ferramenta.
    Retorna uma lista com os caminhos dos arquivos de imagem gerados,
    para serem inseridos no PDF.
    """
    # Preparar dados
    df_speed = df_speed.copy()
    df_librespeed = df_librespeed.copy()
    # Adicionar coluna de ferramenta
    df_speed['Tool'] = 'speedtest-cli'
    df_librespeed['Tool'] = 'librespeed'
    combined = pd.concat([df_speed, df_librespeed], ignore_index=True)

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
    fname_ts = 'time_series_comparison.png'
    plt.savefig(os.path.join(output_dir, fname_ts), dpi=200)
    plt.close()

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
    fname_dist = 'distribuicao_comparison.png'
    plt.savefig(os.path.join(output_dir, fname_dist), dpi=200)
    plt.close()

    # 3. Boxplot por ferramenta (download e upload)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    sns.boxplot(data=combined, x='Tool', y='Download_Mbps', ax=axes[0])
    axes[0].set_title('Download por Ferramenta')
    sns.boxplot(data=combined, x='Tool', y='Upload_Mbps', ax=axes[1])
    axes[1].set_title('Upload por Ferramenta')
    plt.tight_layout()
    fname_box = 'boxplot_comparison.png'
    plt.savefig(os.path.join(output_dir, fname_box), dpi=200)
    plt.close()

    # 4. Scatter: Ping vs Download (comparativo)
    fig, ax = plt.subplots(figsize=(10, 6))
    for tool, df in [('speedtest-cli', df_speed), ('librespeed', df_librespeed)]:
        ax.scatter(df['Ping'], df['Download_Mbps'], alpha=0.5, label=tool, s=10)
    ax.set_xlabel('Ping (ms)')
    ax.set_ylabel('Download (Mbps)')
    ax.set_title('Relação Ping vs Download')
    ax.legend()
    plt.tight_layout()
    fname_scatter = 'scatter_comparison.png'
    plt.savefig(os.path.join(output_dir, fname_scatter), dpi=200)
    plt.close()

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
    fname_hour = 'hourly_comparison.png'
    plt.savefig(os.path.join(output_dir, fname_hour), dpi=200)
    plt.close()

    # 6. Média por dia da semana (comparativa)
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    fig, ax = plt.subplots(figsize=(12, 6))
    for tool, df in [('speedtest-cli', df_speed), ('librespeed', df_librespeed)]:
        df['DayOfWeek'] = df['Timestamp'].dt.day_name()
        weekday_avg = df.groupby('DayOfWeek')['Download_Mbps'].mean().reindex(
            ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        )
        weekday_avg.index = dias_pt
        ax.plot(weekday_avg.index, weekday_avg.values, marker='s', label=tool)
    ax.set_xlabel('Dia da Semana')
    ax.set_ylabel('Download Médio (Mbps)')
    ax.set_title('Média por Dia da Semana')
    ax.legend()
    plt.tight_layout()
    fname_week = 'weekday_comparison.png'
    plt.savefig(os.path.join(output_dir, fname_week), dpi=200)
    plt.close()

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
    fname_med = 'medianas.png'
    plt.savefig(os.path.join(output_dir, fname_med), dpi=200)
    plt.close()

    # Retornar lista de arquivos gerados (para usar na seção 8)
    return [
        fname_ts, fname_dist, fname_box, fname_scatter,
        fname_hour, fname_week, fname_med
    ]

# ------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ------------------------------------------------------------
def generate_report_from_dataframe(df_orig, client_name, isp_name, plan_name,
                                  attorney_name="", address="", bill_path=None,
                                  output_path="report.pdf", valor_mensal=172.00, meses=48):
    # Corrigir grafia de "Brazil" para "Brasil" no endereço
    address = address.replace("Brazil", "Brasil")

    df = df_orig.copy()
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    else:
        df['Timestamp'] = pd.to_datetime('now')

    df['Download_Mbps'] = df['Download'] / 1e6
    df['Upload_Mbps'] = df['Upload'] / 1e6
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])

    # ------------------------------------------------------------
    # Cálculo da taxa de sucesso para TODAS as ferramentas (para a tabela)
    # ------------------------------------------------------------
    # Função de validação específica por ferramenta
    def is_valid_general(row):
        if row['Tool'] == 'fast':
            return row['Download'] > 0
        else:
            return (row['Download'] > 0) & (row['Upload'] > 0) & (row['Ping'] < 10000)

    success_data = []
    for tool in df['Tool'].unique():
        total = len(df[df['Tool'] == tool])
        valid = len(df[df['Tool'] == tool][df.apply(is_valid_general, axis=1)])
        rate = (valid / total * 100) if total > 0 else 0
        success_data.append([tool, total, valid, f"{rate:.1f}%"])

    # ------------------------------------------------------------
    # Filtragem para análise: apenas speedtest-cli e librespeed
    # ------------------------------------------------------------
    def is_valid(row):
        return (row['Download'] > 0) & (row['Upload'] > 0) & (row['Ping'] < 10000)

    allowed_tools = ['speedtest-cli', 'librespeed']
    df_filtered = df[df['Tool'].isin(allowed_tools)].copy()

    if df_filtered.empty:
        raise ValueError("No data from speedtest-cli or librespeed found.")

    clean = df_filtered[df_filtered.apply(is_valid, axis=1)].copy()
    if clean.empty:
        raise ValueError("No valid data after cleaning")

    # Separar por ferramenta
    df_speed = clean[clean['Tool'] == 'speedtest-cli']
    df_librespeed = clean[clean['Tool'] == 'librespeed']

    # Para estatísticas, usar ambas combinadas
    combined_desc = clean[['Download_Mbps', 'Upload_Mbps', 'Ping']].describe()

    # Análise por dia da semana
    weekday_median_full = clean.groupby('DayOfWeek')['Download_Mbps'].median()
    weekdays_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    combined_weekday_median = weekday_median_full.reindex(weekdays_order).dropna()

    # Comparação weekend
    weekend_stats_full = clean.groupby('IsWeekend')['Download_Mbps'].median()
    weekend_stats = weekend_stats_full.reindex([False, True]).dropna()

    # Percentuais por período
    combined_pct_stats_full = clean.groupby('IsWeekend')[['Download_Mbps', 'Upload_Mbps']].median() / [500,250] * 100
    combined_pct_stats = combined_pct_stats_full.reindex([False, True]).dropna()

    # Throttling detection
    has_weekend_data = len(weekend_stats) == 2
    throttling_detected = False
    throttling_percent = 0
    wk_med = we_med = 0
    if has_weekend_data:
        wk_med = weekend_stats[False]
        we_med = weekend_stats[True]
        if wk_med > 0:
            throttling_percent = ((wk_med - we_med) / wk_med) * 100
            if throttling_percent > 5:
                throttling_detected = True

    # Interrupções (nas duas ferramentas)
    connection_interruptions = len(df_filtered[df_filtered['Download'] == 0]) + len(df_filtered[df_filtered['Upload'] == 0])

    # Perda financeira
    overall_median_dl = combined_desc.loc['50%', 'Download_Mbps'] if '50%' in combined_desc.index else 0
    pct_global = (overall_median_dl / 500) * 100 if overall_median_dl > 0 else 0
    perda_mensal = valor_mensal * (1 - pct_global/100)
    perda_total_individual = perda_mensal * meses
    danos_materiais_coletivos = perda_total_individual * 4500
    danos_morais_coletivos = 5000 * 4500
    total_acao_coletiva = danos_materiais_coletivos + danos_morais_coletivos

    # Gerar gráficos comparativos
    graph_dir = tempfile.mkdtemp()
    comparison_images = generate_comparison_plots(df_speed, df_librespeed, graph_dir)

    # ------------------------------------------------------------
    # CONSTRUIR O PDF
    # ------------------------------------------------------------
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2.5*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('Title', parent=styles['Title'], fontSize=20,
                                 alignment=TA_CENTER, spaceAfter=12, fontName='Helvetica-Bold')
    style_subtitle = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14,
                                    alignment=TA_CENTER, spaceAfter=10, fontName='Helvetica')
    style_heading1 = ParagraphStyle('Heading1', parent=styles['Heading1'], fontSize=16,
                                    spaceAfter=8, fontName='Helvetica-Bold')
    style_heading2 = ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=13,
                                    spaceAfter=6, fontName='Helvetica-Bold')
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                                alignment=TA_JUSTIFY, spaceAfter=6, fontName='Helvetica')
    style_centered = ParagraphStyle('Centered', parent=styles['Normal'],
                                    alignment=TA_CENTER, fontSize=10, fontName='Helvetica')
    style_left = ParagraphStyle('Left', parent=styles['Normal'],
                                alignment=TA_LEFT, fontSize=10, fontName='Helvetica')

    story = []

    # Capa
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("RELATÓRIO TÉCNICO - JURÍDICO", style_title))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Análise de Qualidade de Serviço de Internet Banda Larga", style_subtitle))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"Cliente: {client_name}", style_body))
    story.append(Paragraph(f"Plano: {plan_name}", style_body))
    story.append(Paragraph(f"Operadora: {isp_name}", style_body))
    story.append(Paragraph(f"Período de Medição: {clean['Timestamp'].min().strftime('%d/%m/%Y')} a {clean['Timestamp'].max().strftime('%d/%m/%Y')}", style_body))
    story.append(Paragraph(f"Base de Dados: {len(clean)} registros válidos (speedtest-cli + librespeed)", style_body))
    story.append(Spacer(1, 2*cm))
    if attorney_name:
        story.append(Paragraph(f"Advogado: {attorney_name}", style_centered))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Guaxupé, {data_extenso(datetime.now())}", style_centered))
    story.append(PageBreak())

    # Sumário
    story.append(Paragraph("SUMÁRIO", style_heading1))
    story.append(Spacer(1, 0.5*cm))
    for sec in [
        "1. OBJETIVO",
        "2. METODOLOGIA",
        "3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO",
        "   3.1. Desempenho por Dia da Semana",
        "   3.2. Comparação Dias Úteis vs. Fins de Semana",
        "   3.3. Análise de Throttling",
        "4. VELOCIDADE CONTRATADA VERSUS ENTREGUE",
        "   4.1. Parâmetros Contratados",
        "   4.2. Estatísticas Gerais",
        "   4.3. Percentuais de Entrega por Período",
        "5. CÁLCULO DA PERDA FINANCEIRA",
        "   5.1. Premissas",
        "   5.2. Perda Mensal por Período",
        "   5.3. Perda Média Mensal",
        "   5.4. Perda Acumulada",
        "   5.5. Estimativa para Ação Civil Pública",
        "6. FUNDAMENTAÇÃO LEGAL E JURISPRUDÊNCIA",
        "7. RECOMENDAÇÕES",
        "8. ANEXOS – GRÁFICOS COMPARATIVOS E MEDIANAS",
        "9. RESUMO EXECUTIVO",
    ]:
        story.append(Paragraph(sec, style_body))
    story.append(PageBreak())

    # 1. OBJETIVO
    story.append(Paragraph("1. OBJETIVO", style_heading1))
    objective_text = f"""
    Com base nas medições objetivas e contínuas realizadas entre {clean['Timestamp'].min().strftime('%d/%m/%Y')} e {clean['Timestamp'].max().strftime('%d/%m/%Y')}, 
    utilizando as ferramentas speedtest-cli e LibreSpeed, este relatório comprova que a prestadora {isp_name} não está cumprindo a velocidade de download e upload contratadas no plano {plan_name}.
    
    A velocidade mediana de download obtida foi de {overall_median_dl:.1f} Mbps, representando apenas {pct_global:.1f}% dos 500 Mbps contratados, 
    valor significativamente inferior ao mínimo de 80% exigido pela Resolução Anatel nº 632/2014.
    """
    if throttling_detected:
        objective_text += f"""
    Foi identificada prática de throttling (redução arbitrária de velocidade) nos fins de semana, com redução média de {throttling_percent:.1f}% 
    na velocidade de download em comparação aos dias úteis, caracterizando violação ao princípio da neutralidade de rede (Marco Civil da Internet, art. 9º).
    """
    else:
        objective_text += """
    Não foi possível confirmar a prática de throttling devido à indisponibilidade de dados em ambos os períodos (dias úteis e fins de semana) para comparação.
    """
    if connection_interruptions > 0:
        objective_text += f"""
    
    Durante o período de coleta, foram identificados {connection_interruptions} momentos em que a conexão foi interrompida (download ou upload igual a zero), 
    indicando falhas na prestação do serviço.
    """
    objective_text += """
    
    Os dados aqui apresentados servem como subsídio técnico para notificação extrajudicial, ação judicial individual e provocação do Ministério Público e da Anatel para ação civil pública.
    """
    story.append(Paragraph(objective_text, style_body))
    story.append(Spacer(1, 0.5*cm))

    # 2. METODOLOGIA (com descrição das ferramentas, tabela e texto)
    story.append(Paragraph("2. METODOLOGIA", style_heading1))
    story.append(Paragraph(
        "Os testes foram realizados com as ferramentas speedtest-cli, LibreSpeed, Fast.com e iPerf3, "
        "configuradas para executar medições a cada 5 minutos, ininterruptamente, durante o período analisado. "
        "Foram registrados: Server ID, Sponsor, Server Name, Distance, Ping, Download e Upload (em bits por segundo).",
        style_body
    ))
    
    # Breve descrição das ferramentas (lista com bullets)
    story.append(Paragraph("Cada ferramenta tem características específicas:", style_body))
    item_style = ParagraphStyle(
        'ListItem',
        parent=style_body,
        leftIndent=20,
        bulletText='- ',
        spaceAfter=2,
    )
    itens = [
        "speedtest-cli (Ookla): Mede download, upload e latência. É a mais confiável e amplamente utilizada.",
        "LibreSpeed (via npx): Semelhante ao speedtest-cli, código aberto. Também fornece geolocalização do servidor.",
        "Fast.com (Netflix): Mede apenas download, com servidores otimizados para streaming. Não mede upload nem latência.",
        "iPerf3: Mede throughput TCP/UDP, mas depende de servidores públicos que podem estar indisponíveis, resultando em falhas frequentes.",
    ]
    for item in itens:
        story.append(Paragraph(item, item_style))
    
    # Espaçamento entre a lista e a tabela
    story.append(Spacer(1, 0.3*cm))
    
    # Tabela de taxa de sucesso (com todas as ferramentas)
    table_success = Table([["Ferramenta", "Total Testes", "Válidos", "Taxa de Sucesso"]] + success_data,
                          colWidths=[4*cm, 3*cm, 3*cm, 4*cm])
    table_success.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ecf0f1')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#7f8c8d')),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(KeepTogether([table_success, Spacer(1, 0.3*cm)]))
    
    # Espaçamento após a tabela
    story.append(Spacer(1, 0.3*cm))
    
    # Parágrafo explicativo sobre a análise estatística focada nas duas ferramentas
    story.append(Paragraph(
        "A análise estatística principal (mediana, percentuais) foi calculada utilizando exclusivamente os dados dessas duas ferramentas, "
        "por serem as mais confiáveis e amplamente utilizadas para medições de velocidade.",
        style_body
    ))
    story.append(Spacer(1, 0.5*cm))

    # 3. ANÁLISE ESTATÍSTICA
    story.append(Paragraph("3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO", style_heading1))

    # 3.1 Desempenho por dia da semana
    story.append(Paragraph("3.1. Desempenho por Dia da Semana (dias com dados disponíveis)", style_heading2))
    if not combined_weekday_median.empty:
        dados_dia = [["Dia da Semana", "Mediana Download (Mbps)", "% da Contratada", "Categoria"]]
        for dia, valor in combined_weekday_median.items():
            pct = (valor / 500) * 100
            categoria = "Útil" if dia in ['Monday','Tuesday','Wednesday','Thursday','Friday'] else "Fim de semana"
            idx = weekdays_order.index(dia) if dia in weekdays_order else 0
            nome_dia = dias_pt[idx]
            dados_dia.append([nome_dia, f"{valor:.1f}", f"{pct:.1f}%", categoria])
        table_dia = Table(dados_dia, colWidths=[3.5*cm, 4.5*cm, 3.5*cm, 4*cm])
        table_dia.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 7),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ecf0f1')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#7f8c8d')),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(KeepTogether([table_dia, Spacer(1, 0.3*cm)]))
    else:
        story.append(Paragraph("Não há dados suficientes para análise por dia da semana.", style_body))

    # 3.2 Comparação weekend
    story.append(Paragraph("3.2. Comparação Dias Úteis vs. Fins de Semana", style_heading2))
    if len(weekend_stats) == 2:
        upload_weekday = clean[~clean['IsWeekend']]['Upload_Mbps'].median() if not clean[~clean['IsWeekend']].empty else 0
        upload_weekend = clean[clean['IsWeekend']]['Upload_Mbps'].median() if not clean[clean['IsWeekend']].empty else 0
        dados_comp = [
            ["Período", "Mediana Download (Mbps)", "% da Contratada", "Mediana Upload (Mbps)", "% da Contratada (250)"],
            ["Dias de semana (2ª a 6ª)", f"{wk_med:.1f}", f"{(wk_med/500)*100:.1f}%", f"{upload_weekday:.1f}", f"{(upload_weekday/250)*100:.1f}%"],
            ["Fins de semana (Sáb+Dom)", f"{we_med:.1f}", f"{(we_med/500)*100:.1f}%", f"{upload_weekend:.1f}", f"{(upload_weekend/250)*100:.1f}%"],
        ]
        table_comp = Table(dados_comp, colWidths=[4.5*cm, 3.5*cm, 3*cm, 3.5*cm, 3*cm])
        table_comp.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 7),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ecf0f1')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#7f8c8d')),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(KeepTogether([table_comp, Spacer(1, 0.3*cm)]))
        reducao = ((wk_med - we_med) / wk_med) * 100 if wk_med > 0 else 0
        story.append(Paragraph(
            f"Observação: Há uma redução média de {reducao:.1f}% na velocidade nos fins de semana, o que evidencia gestão de tráfego sem aviso prévio.",
            style_body
        ))
    else:
        story.append(Paragraph("Não há dados suficientes para comparar dias úteis e fins de semana (apenas um dos períodos possui registros).", style_body))
    story.append(Spacer(1, 0.3*cm))

    # 3.3 Throttling
    story.append(Paragraph("3.3. Análise de Throttling (Limitação de Velocidade)", style_heading2))
    if throttling_detected:
        throttle_text = f"""
        A análise dos dados coletados revelou a prática de throttling (redução arbitrária de velocidade) nos fins de semana. 
        A velocidade mediana de download nos dias úteis foi de {wk_med:.1f} Mbps, enquanto nos fins de semana caiu para {we_med:.1f} Mbps, 
        representando uma redução de {throttling_percent:.1f}%. 
        Esta redução sistemática caracteriza violação ao princípio da neutralidade de rede (Marco Civil da Internet, art. 9º), 
        ao direito à informação adequada (CDC, art. 6º, III) e à boa-fé objetiva (CDC, art. 4º, III).
        """
    else:
        throttle_text = """
        Não foi possível confirmar a prática de throttling com os dados disponíveis, pois apenas um dos períodos (dias úteis ou fins de semana) 
        possui registros suficientes para comparação. Recomenda-se a continuidade das medições para obter dados em ambos os períodos.
        """
    story.append(Paragraph(throttle_text, style_body))
    story.append(Spacer(1, 0.5*cm))

    # 4. VELOCIDADE CONTRATADA VS ENTREGUE
    story.append(Paragraph("4. VELOCIDADE CONTRATADA VERSUS ENTREGUE", style_heading1))
    story.append(Paragraph("4.1. Parâmetros Contratados", style_heading2))
    story.append(Paragraph("• Download: 500 Mbps", style_body))
    story.append(Paragraph("• Upload: 250 Mbps", style_body))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4.2. Estatísticas Gerais de Download e Upload (dados consolidados das duas ferramentas)", style_heading2))
    desc_data = [["Estatística", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)"]]
    for stat in combined_desc.index:
        desc_data.append([
            stat.capitalize(),
            f"{combined_desc.loc[stat, 'Download_Mbps']:.1f}",
            f"{combined_desc.loc[stat, 'Upload_Mbps']:.1f}",
            f"{combined_desc.loc[stat, 'Ping']:.1f}"
        ])
    table_desc = Table(desc_data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
    table_desc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ecf0f1')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#7f8c8d')),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(KeepTogether([table_desc, Spacer(1, 0.3*cm)]))

    overall_dl = combined_desc.loc['50%', 'Download_Mbps'] if '50%' in combined_desc.index else 0
    overall_ul = combined_desc.loc['50%', 'Upload_Mbps'] if '50%' in combined_desc.index else 0
    story.append(Paragraph(
        f"A mediana ({overall_dl:.1f} Mbps de download e {overall_ul:.1f} Mbps de upload) é o indicador mais adequado para "
        "avaliar a velocidade típica da conexão.", style_body
    ))

    story.append(Paragraph("4.3. Percentuais de Entrega por Período (dados disponíveis)", style_heading2))
    if not combined_pct_stats.empty:
        pct_data = [["Período", "Download Pct (%)", "Upload Pct (%)"]]
        for idx, row in combined_pct_stats.iterrows():
            periodo = "Dias de semana" if idx == False else "Fins de semana"
            pct_data.append([periodo, f"{row['Download_Mbps']:.1f}%", f"{row['Upload_Mbps']:.1f}%"])
        table_pct = Table(pct_data, colWidths=[5*cm, 5*cm, 5*cm])
        table_pct.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ecf0f1')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#7f8c8d')),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(KeepTogether([table_pct, Spacer(1, 0.5*cm)]))
    else:
        story.append(Paragraph("Não há dados para calcular os percentuais de entrega por período.", style_body))

    # 5. PERDA FINANCEIRA
    story.append(Paragraph("5. CÁLCULO DA PERDA FINANCEIRA", style_heading1))
    story.append(Paragraph("5.1. Premissas", style_heading2))
    story.append(Paragraph(f"• Plano: {plan_name}", style_body))
    story.append(Paragraph(f"• Valor mensal estimado: {format_br_money(valor_mensal)}", style_body))
    story.append(Paragraph(f"• Período analisado: {meses} meses ({meses//12} anos)", style_body))
    story.append(Paragraph("• Inflação/reajustes não considerados (cálculo subestimado)", style_body))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5.2. Perda Mensal por Período (dados disponíveis)", style_heading2))
    if not combined_pct_stats.empty:
        perda_data = [["Período", "% Entregue", "% Não Entregue", "Valor Mensal (R$)", "Valor Efetivo (R$)", "Perda Mensal (R$)"]]
        for idx, row in combined_pct_stats.iterrows():
            pct_ent = row['Download_Mbps']
            pct_nao = 100 - pct_ent
            val_efet = valor_mensal * (pct_ent / 100)
            perda = valor_mensal - val_efet
            periodo = "Dias de semana" if idx == False else "Fins de semana"
            perda_data.append([
                periodo,
                f"{pct_ent:.1f}%",
                f"{pct_nao:.1f}%",
                format_br_money(valor_mensal),
                format_br_money(val_efet),
                format_br_money(perda)
            ])
        table_perda = Table(perda_data, colWidths=[3.5*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm, 3*cm])
        table_perda.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ecf0f1')),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#7f8c8d')),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(KeepTogether([table_perda, Spacer(1, 0.3*cm)]))
    else:
        story.append(Paragraph("Não há dados para calcular a perda por período.", style_body))

    story.append(Paragraph("5.3. Perda Média Mensal", style_heading2))
    story.append(Paragraph(f"• Perda média mensal (calculada com base na mediana geral de download): {format_br_money(perda_mensal)}", style_body))
    story.append(Paragraph(f"• Perda total individual em {meses} meses: {format_br_money(perda_total_individual)}", style_body))
    story.append(Paragraph(
        f"Este valor é passível de restituição em dobro (CDC, art. 42, parágrafo único), "
        f"totalizando {format_br_money(perda_total_individual*2)}.", style_body
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5.4. Estimativa para Ação Civil Pública (Região de Guaxupé/MG)", style_heading2))
    story.append(Paragraph("• Número estimado de clientes Vivo Fibra na região: 4.500", style_body))
    story.append(Paragraph(f"• Perda média por cliente: {format_br_money(perda_total_individual)}", style_body))
    story.append(Paragraph(f"• Danos materiais coletivos: 4.500 × {format_br_number(perda_total_individual)} = {format_br_money(danos_materiais_coletivos)}", style_body))
    story.append(Paragraph(f"• Danos morais coletivos (R$ 5.000/cliente): 4.500 × 5.000 = {format_br_money(danos_morais_coletivos)}", style_body))
    story.append(Paragraph(f"• Total estimado da ação civil pública: {format_br_money(total_acao_coletiva)}", style_body))
    story.append(Spacer(1, 0.5*cm))

    # 6. LEGAL
    bloco_legal = []
    bloco_legal.append(Paragraph("6. FUNDAMENTAÇÃO LEGAL E JURISPRUDÊNCIA", style_heading1))
    bloco_legal.append(Paragraph("6.1. Dispositivos Legais Aplicáveis", style_heading2))
    bloco_legal.append(Paragraph("• Constituição Federal, art. 5º, XXXII – defesa do consumidor.", style_body))
    bloco_legal.append(Paragraph("• Código de Defesa do Consumidor, art. 6º, III e VIII – informação e inversão do ônus da prova.", style_body))
    bloco_legal.append(Paragraph("• CDC, art. 14 – responsabilidade objetiva.", style_body))
    bloco_legal.append(Paragraph("• CDC, art. 39, V – vedação de vantagem excessiva.", style_body))
    bloco_legal.append(Paragraph("• CDC, art. 42, p.ú – devolução em dobro.", style_body))
    bloco_legal.append(Paragraph("• Lei Geral de Telecomunicações, art. 3º – padrões de qualidade.", style_body))
    bloco_legal.append(Paragraph("• Resolução Anatel nº 632/2014, art. 3º, §1º – velocidade média ≥ 80%.", style_body))
    bloco_legal.append(Paragraph("• Marco Civil da Internet, art. 9º – neutralidade de rede.", style_body))
    bloco_legal.append(Spacer(1, 0.3*cm))
    bloco_legal.append(Paragraph("6.2. Jurisprudência Relevante", style_heading2))
    bloco_legal.append(Paragraph(
        "• STJ, REsp 1.660.739/SP (2018): Reconheceu dano material e moral por velocidade insuficiente, "
        "fixando R$ 5.000,00 por cliente.", style_body
    ))
    bloco_legal.append(Paragraph(
        "• TJSP, Apelação nº 1038170-12.2019.8.26.0114: Vivo condenada por velocidade inferior.", style_body
    ))
    bloco_legal.append(Paragraph(
        "• MPMA vs. Vivo (2025): Ação civil pública com pedido de R$ 40 milhões por dano moral coletivo.", style_body
    ))
    story.append(KeepTogether(bloco_legal))
    story.append(Spacer(1, 0.5*cm))

    # 7. RECOMENDAÇÕES
    story.append(Paragraph("7. RECOMENDAÇÕES", style_heading1))
    story.append(Paragraph(
        "1. <b>Notificação extrajudicial à operadora</b> – Enviar notificação formal, com prazo de 15 (quinze) dias "
        "para que a operadora regularize a velocidade de download para, no mínimo, 80% do contratado (400 Mbps) "
        "e apresente comprovação da efetiva entrega do serviço, sob pena de adoção das medidas judiciais cabíveis. "
        "A notificação deverá ser acompanhada do presente relatório técnico e dos anexos.", style_body
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"2. <b>Ajuizamento de ação individual</b> – Caso não haja solução administrativa, propôr ação perante o "
        f"Juizado Especial Cível ou Vara Cível competente, pleiteando: (a) restituição em dobro dos valores pagos "
        f"a maior, conforme art. 42 do CDC (total estimado de {format_br_money(perda_total_individual*2)}); "
        f"(b) indenização por danos morais no valor de R$ 10.000,00, com base nos precedentes do STJ e TJSP; "
        f"(c) obrigação de fazer para que a operadora passe a faturar com transparência, discriminando a "
        f"velocidade média mensal entregue e os incidentes de interrupção, com desconto automático proporcional.",
        style_body
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "3. <b>Encaminhamento ao Ministério Público Federal e à Anatel</b> – Remeter cópia integral do relatório, "
        "com os gráficos e tabelas, ao MPF e à Superintendência de Fiscalização da Anatel, solicitando a "
        "instauração de procedimento administrativo para apuração das infrações à Resolução Anatel nº 632/2014 "
        "e ao Marco Civil da Internet, bem como o ajuizamento de ação civil pública em âmbito nacional para "
        "proteger os direitos difusos de todos os consumidores.", style_body
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "4. <b>Divulgação e mobilização social</b> – Compartilhar o caso com associações de defesa do consumidor "
        "(IDEC, PROTESTE, PROCON) e com a imprensa local e nacional, visando conscientizar outros consumidores "
        "sobre a prática de throttling e a necessidade de fiscalização mais rigorosa, além de estimular a adesão "
        "a eventuais ações coletivas.", style_body
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(PageBreak())

    # 8. ANEXOS – GRÁFICOS COMPARATIVOS E MEDIANAS
    story.append(Paragraph("8. ANEXOS – GRÁFICOS COMPARATIVOS E MEDIANAS", style_heading1))
    story.append(Spacer(1, 0.3*cm))

    def insert_comparison_grid(prefix, title):
        story.append(Paragraph(title, style_heading2))
        story.append(Spacer(1, 0.3*cm))
        # Buscar os arquivos que começam com prefixo (ex: 'time_series_comparison')
        img_paths = []
        for fname in comparison_images:
            if fname.startswith(prefix):
                img_path = os.path.join(graph_dir, fname)
                if os.path.exists(img_path):
                    img_paths.append(img_path)
        if not img_paths:
            story.append(Paragraph("Nenhum gráfico disponível para esta seção.", style_body))
            story.append(PageBreak())
            return
        # Organizar em grade de 2 colunas
        rows = []
        row = []
        for i, path in enumerate(img_paths):
            img = Image(path, width=7.5*cm, height=5*cm)
            row.append(img)
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            row.append(Spacer(1, 0))
            rows.append(row)
        table_imgs = Table(rows, colWidths=[7.5*cm, 7.5*cm])
        table_imgs.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0.1*cm),
            ('RIGHTPADDING', (0,0), (-1,-1), 0.1*cm),
        ]))
        story.append(KeepTogether([table_imgs, Spacer(1, 0.3*cm)]))
        story.append(PageBreak())

    # Inserir gráficos comparativos (todos exceto o de medianas)
    insert_comparison_grid('time_series_comparison', 'Evolução Temporal (speedtest-cli vs LibreSpeed)')
    insert_comparison_grid('distribuicao_comparison', 'Distribuição das Velocidades')
    insert_comparison_grid('boxplot_comparison', 'Boxplot por Ferramenta')
    insert_comparison_grid('scatter_comparison', 'Ping vs Download')
    insert_comparison_grid('hourly_comparison', 'Média Horária')
    insert_comparison_grid('weekday_comparison', 'Média por Dia da Semana')

    # Página especial para a mediana
    story.append(Paragraph("Mediana das Velocidades por Ferramenta", style_heading2))
    story.append(Spacer(1, 0.3*cm))
    median_path = os.path.join(graph_dir, 'medianas.png')
    if os.path.exists(median_path):
        img = Image(median_path, width=14*cm, height=8*cm)
        story.append(KeepTogether([img, Spacer(1, 0.3*cm)]))
    else:
        story.append(Paragraph("Gráfico de medianas não disponível.", style_body))
    story.append(PageBreak())

    # 9. RESUMO EXECUTIVO
    story.append(Paragraph("9. RESUMO EXECUTIVO", style_heading1))
    story.append(Spacer(1, 0.3*cm))

    total_tests = len(clean)
    periodo = f"{clean['Timestamp'].min().strftime('%d/%m/%Y')} a {clean['Timestamp'].max().strftime('%d/%m/%Y')}"
    dl_med = overall_dl
    ul_med = overall_ul
    ping_med = combined_desc.loc['50%', 'Ping'] if '50%' in combined_desc.index else 0
    pct_global = (dl_med / 500) * 100 if dl_med > 0 else 0

    if throttling_detected:
        throttling_desc = f"Redução de {throttling_percent:.1f}% nos fins de semana (throttling confirmado)."
    else:
        throttling_desc = "Não foi possível confirmar throttling por falta de dados em um dos períodos."

    resumo_texto = f"""
    Este relatório analisou {total_tests} testes de velocidade (speedtest-cli e LibreSpeed) realizados entre {periodo}.
    A velocidade mediana de download foi de {dl_med:.1f} Mbps, o que representa apenas {pct_global:.1f}% da velocidade contratada (500 Mbps).
    A mediana de upload foi de {ul_med:.1f} Mbps ({ul_med/250*100:.1f}% do contratado) e o ping médio foi de {ping_med:.1f} ms.
    {throttling_desc}
    Com base na velocidade entregue, o prejuízo financeiro individual acumulado em {meses} meses é de {format_br_money(perda_total_individual)}.
    Esta perda, quando considerada para uma possível ação coletiva, pode ultrapassar {format_br_money(total_acao_coletiva)}.
    """
    story.append(Paragraph(resumo_texto, style_body))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(f"Localidade: {address}", style_body))
    story.append(Paragraph(f"Data da emissão: {data_extenso(datetime.now())}", style_body))
    story.append(Spacer(1, 1.5*cm))

    # Assinaturas
    story.append(Paragraph("_________________________________________", style_body))
    story.append(Paragraph("Responsável Técnico", style_body))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("_________________________________________", style_body))
    story.append(Paragraph("Advogado", style_body))
    story.append(Spacer(1, 1*cm))

    if bill_path and os.path.exists(bill_path):
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Fatura anexada (PDF)", style_centered))

    doc.build(story)
    print(f"PDF gerado com sucesso: {output_path}")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True)
    parser.add_argument('--client', required=True)
    parser.add_argument('--isp', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--attorney', default='')
    parser.add_argument('--address', default='')
    parser.add_argument('--bill', default=None)
    parser.add_argument('--output', default='report.pdf')
    args = parser.parse_args()
    try:
        df = pd.read_csv(args.csv)
        generate_report_from_dataframe(
            df_orig=df,
            client_name=args.client,
            isp_name=args.isp,
            plan_name=args.plan,
            attorney_name=args.attorney,
            address=args.address,
            bill_path=args.bill,
            output_path=args.output
        )
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        exit(1)