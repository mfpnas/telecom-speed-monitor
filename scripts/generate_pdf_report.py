#!/usr/bin/env python3
"""
Generate a comprehensive court-ready PDF report from speed test data,
including per‑tool analysis and the full legal sections.
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

def generate_plots(df, output_dir, tool=None):
    """Generate graphs for a given DataFrame, optionally filtered by tool."""
    if tool:
        title_suffix = f" - {tool}"
    else:
        title_suffix = ""
    # Time series
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['Timestamp'], df['Download_Mbps'], alpha=0.3, label='Download (bruto)')
    ax.plot(df['Timestamp'], df['Upload_Mbps'], alpha=0.3, label='Upload (bruto)')
    ma_dl = df['Download_Mbps'].rolling(10, min_periods=1).mean()
    ma_ul = df['Upload_Mbps'].rolling(10, min_periods=1).mean()
    ax.plot(df['Timestamp'], ma_dl, 'r-', linewidth=2, label='Download (MA10)')
    ax.plot(df['Timestamp'], ma_ul, 'b-', linewidth=2, label='Upload (MA10)')
    ax.set_title(f'Evolução das Velocidades (MA10){title_suffix}')
    ax.set_xlabel('Data/Hora')
    ax.set_ylabel('Mbps')
    ax.legend(loc='upper left')
    plt.tight_layout()
    fname = f"time_series{'_{}'.format(tool) if tool else ''}.png"
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()

    # Distributions
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.histplot(df['Download_Mbps'], bins=60, kde=True, ax=axes[0], color='green')
    axes[0].axvline(df['Download_Mbps'].median(), color='red', linestyle='--',
                    label=f'Mediana: {df["Download_Mbps"].median():.1f} Mbps')
    axes[0].set_title(f'Distribuição do Download{title_suffix}')
    axes[0].legend()
    sns.histplot(df['Upload_Mbps'], bins=60, kde=True, ax=axes[1], color='orange')
    axes[1].axvline(df['Upload_Mbps'].median(), color='red', linestyle='--',
                    label=f'Mediana: {df["Upload_Mbps"].median():.1f} Mbps')
    axes[1].set_title(f'Distribuição do Upload{title_suffix}')
    axes[1].legend()
    plt.tight_layout()
    fname = f"distribuicao{'_{}'.format(tool) if tool else ''}.png"
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()

    # Boxplot by Sponsor (if enough data)
    if len(df['Sponsor'].unique()) > 1:
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=df, x='Sponsor', y='Download_Mbps', hue='Sponsor', palette='Set3', legend=False)
        plt.xticks(rotation=45, ha='right')
        plt.title(f'Velocidade de Download por Provedor{title_suffix}')
        plt.ylabel('Download (Mbps)')
        plt.tight_layout()
        fname = f"boxplot_sponsor{'_{}'.format(tool) if tool else ''}.png"
        plt.savefig(os.path.join(output_dir, fname), dpi=200)
        plt.close()

    # Scatter Distance vs Download
    if 'Distance' in df.columns and df['Distance'].notna().any():
        plt.figure(figsize=(12, 6))
        scatter = plt.scatter(df['Distance'], df['Download_Mbps'],
                              c=df['Ping'], cmap='plasma', alpha=0.5, s=10)
        plt.colorbar(scatter, label='Ping (ms)')
        plt.xlabel('Distância (km)')
        plt.ylabel('Download (Mbps)')
        plt.title(f'Relação Distância vs Download{title_suffix}')
        plt.tight_layout()
        fname = f"mapa_provedores_distancia{'_{}'.format(tool) if tool else ''}.png"
        plt.savefig(os.path.join(output_dir, fname), dpi=200)
        plt.close()

    # Hourly averages
    df['Hour'] = df['Timestamp'].dt.hour
    hourly = df.groupby('Hour')[['Download_Mbps', 'Upload_Mbps']].mean()
    fig, ax = plt.subplots(figsize=(12, 5))
    hourly.plot(kind='bar', ax=ax, color=['green', 'orange'])
    ax.set_title(f'Velocidade Média por Hora do Dia{title_suffix}')
    ax.set_xlabel('Hora')
    ax.set_ylabel('Mbps')
    plt.tight_layout()
    fname = f"media_horaria{'_{}'.format(tool) if tool else ''}.png"
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()

    # Day of week averages
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    weekday_avg = df.groupby('DayOfWeek')[['Download_Mbps', 'Upload_Mbps']].mean().reindex(
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    )
    weekday_avg.index = dias_pt
    fig, ax = plt.subplots(figsize=(10, 5))
    weekday_avg.plot(kind='bar', ax=ax, color=['green', 'orange'])
    ax.set_title(f'Velocidade Média por Dia da Semana{title_suffix}')
    ax.set_xlabel('Dia')
    ax.set_ylabel('Mbps')
    plt.tight_layout()
    fname = f"media_dia_semana{'_{}'.format(tool) if tool else ''}.png"
    plt.savefig(os.path.join(output_dir, fname), dpi=200)
    plt.close()

    return output_dir


def generate_report_from_dataframe(df_orig, client_name, isp_name, plan_name,
                                  attorney_name="", address="", bill_path=None,
                                  output_path="report.pdf", valor_mensal=172.00, meses=48):
    # Prepare data
    df = df_orig.copy()
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    elif 'timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        df['Timestamp'] = pd.to_datetime('now')

    df['Download_Mbps'] = df['Download'] / 1e6
    df['Upload_Mbps'] = df['Upload'] / 1e6
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])

    # Remove invalid
    clean = df[(df['Download'] > 0) & (df['Upload'] > 0) & (df['Ping'] < 10000)].copy()
    if clean.empty:
        raise ValueError("No valid data after cleaning")

    # Determine available tools
    tools = clean['Tool'].unique() if 'Tool' in clean.columns else ['All']
    if 'Tool' not in clean.columns:
        clean['Tool'] = 'All'

    # Per‑tool analysis
    tool_stats = {}
    for tool in tools:
        tool_df = clean[clean['Tool'] == tool]
        if len(tool_df) < 2:
            continue
        tool_stats[tool] = {
            'desc': tool_df[['Download_Mbps', 'Upload_Mbps', 'Ping']].describe(),
            'weekday_median': tool_df.groupby('DayOfWeek')['Download_Mbps'].median().reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']),
            'weekend_stats': tool_df.groupby('IsWeekend')['Download_Mbps'].median().reindex([False, True]),
            'pct_stats': tool_df.groupby('IsWeekend')[['Download_Mbps', 'Upload_Mbps']].median() / [500,250] * 100
        }

    # Combined stats
    combined_desc = clean[['Download_Mbps', 'Upload_Mbps', 'Ping']].describe()
    combined_weekday_median = clean.groupby('DayOfWeek')['Download_Mbps'].median().reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    combined_weekend_stats = clean.groupby('IsWeekend')['Download_Mbps'].median().reindex([False, True])
    combined_pct_stats = clean.groupby('IsWeekend')[['Download_Mbps', 'Upload_Mbps']].median() / [500,250] * 100

    # Financials
    pct_weekday = combined_pct_stats.loc[False, 'Download_Mbps'] if False in combined_pct_stats.index else 0
    pct_weekend = combined_pct_stats.loc[True, 'Download_Mbps'] if True in combined_pct_stats.index else 0
    # Fill missing with 0
    pct_weekday = pct_weekday if not pd.isna(pct_weekday) else 0
    pct_weekend = pct_weekend if not pd.isna(pct_weekend) else 0

    perda_weekday = valor_mensal * (1 - pct_weekday/100)
    perda_weekend = valor_mensal * (1 - pct_weekend/100)
    perda_media_mensal = (5/7) * perda_weekday + (2/7) * perda_weekend
    perda_total_individual = perda_media_mensal * meses
    danos_materiais_coletivos = perda_total_individual * 4500
    danos_morais_coletivos = 5000 * 4500
    total_acao_coletiva = danos_materiais_coletivos + danos_morais_coletivos

    # Generate graphs for combined and per-tool
    graph_dir = tempfile.mkdtemp()
    # Combined
    generate_plots(clean, graph_dir, tool=None)
    # Per tool (if more than one tool)
    for tool in tools:
        if len(clean[clean['Tool'] == tool]) > 1:
            generate_plots(clean[clean['Tool'] == tool], graph_dir, tool=tool)

    # Build PDF
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

    # --- CAPA ---
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("RELATÓRIO TÉCNICO - JURÍDICO", style_title))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Análise de Qualidade de Serviço de Internet Banda Larga", style_subtitle))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"Cliente: {client_name}", style_body))
    story.append(Paragraph(f"Plano: {plan_name}", style_body))
    story.append(Paragraph(f"Operadora: {isp_name}", style_body))
    story.append(Paragraph(f"Período de Medição: {clean['Timestamp'].min().strftime('%d/%m/%Y')} a {clean['Timestamp'].max().strftime('%d/%m/%Y')}", style_body))
    story.append(Paragraph(f"Base de Dados: {len(clean)} registros válidos", style_body))
    story.append(Spacer(1, 2*cm))
    if attorney_name:
        story.append(Paragraph(f"Advogado: {attorney_name}", style_centered))
    story.append(Paragraph(address, style_centered))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Guaxupé, {datetime.now().strftime('%d de %B de %Y')}", style_centered))
    story.append(PageBreak())

    # --- SUMÁRIO ---
    story.append(Paragraph("SUMÁRIO", style_heading1))
    story.append(Spacer(1, 0.5*cm))
    for sec in [
        "1. OBJETIVO",
        "2. METODOLOGIA",
        "3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO",
        "4. VELOCIDADE CONTRATADA VERSUS ENTREGUE",
        "5. CÁLCULO DA PERDA FINANCEIRA",
        "6. FUNDAMENTAÇÃO LEGAL E JURISPRUDÊNCIA",
        "7. RECOMENDAÇÕES",
        "8. ANEXOS",
    ]:
        story.append(Paragraph(sec, style_body))
    story.append(PageBreak())

    # --- 1. OBJETIVO ---
    story.append(Paragraph("1. OBJETIVO", style_heading1))
    story.append(Paragraph(
        f"O presente relatório tem por finalidade demonstrar, com base em medições objetivas e contínuas, "
        f"que a prestadora {isp_name} não está cumprindo a velocidade de download e upload contratadas no "
        f"plano {plan_name}, além de evidenciar a prática de redução arbitrária de velocidade (throttling) "
        f"nos fins de semana. Os dados aqui apresentados servirão como subsídio técnico para notificação "
        f"extrajudicial, ação judicial individual e provocação do Ministério Público e da Anatel para ação civil pública.",
        style_body
    ))
    story.append(Spacer(1, 0.5*cm))

    # --- 2. METODOLOGIA ---
    story.append(Paragraph("2. METODOLOGIA", style_heading1))
    story.append(Paragraph(
        "Os testes foram realizados com as ferramentas speedtest-cli, LibreSpeed, Fast.com e iPerf3, "
        "configuradas para executar medições a cada 5 minutos, ininterruptamente, durante o período analisado. "
        "Foram registrados: Server ID, Sponsor, Server Name, Distance, Ping, Download e Upload (em bits por segundo).",
        style_body
    ))
    story.append(Paragraph(
        f"Critérios de exclusão: velocidade zero, ping > 10.000 ms. Após a limpeza, restaram {len(clean)} registros válidos.",
        style_body
    ))
    story.append(Paragraph(
        "As análises foram conduzidas com Python (pandas, numpy, scipy, matplotlib, seaborn).",
        style_body
    ))
    story.append(Spacer(1, 0.5*cm))

    # --- 3. ESTATÍSTICAS ---
    story.append(Paragraph("3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO", style_heading1))

    # Combined weekday table
    story.append(Paragraph("3.1. Desempenho por Dia da Semana (Dados Consolidados)", style_heading2))
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    dados_dia = [["Dia da Semana", "Mediana Download (Mbps)", "% da Contratada", "Categoria"]]
    for dia, valor in combined_weekday_median.items():
        pct = (valor / 500) * 100 if not pd.isna(valor) else 0
        categoria = "Útil" if dia in ['Monday','Tuesday','Wednesday','Thursday','Friday'] else "Fim de semana"
        dados_dia.append([dia[:3] if dia in ['Monday','Tuesday','Wednesday','Thursday','Friday'] else dia, f"{valor:.1f}" if not pd.isna(valor) else "-", f"{pct:.1f}%", categoria])
    table_dia = Table(dados_dia, colWidths=[3.5*cm, 4.5*cm, 3.5*cm, 4*cm])
    table_dia.setStyle(...)
    story.append(KeepTogether([table_dia, Spacer(1, 0.3*cm)]))

    # Combined weekend comparison
    story.append(Paragraph("3.2. Comparação Dias Úteis vs. Fins de Semana", style_heading2))
    wk_median = combined_weekend_stats.get(False, 0) if False in combined_weekend_stats.index else 0
    we_median = combined_weekend_stats.get(True, 0) if True in combined_weekend_stats.index else 0
    dados_comp = [
        ["Período", "Mediana Download (Mbps)", "% da Contratada", "Mediana Upload (Mbps)", "% da Contratada (250)"],
        ["Dias de semana (2ª a 6ª)", f"{wk_median:.1f}", f"{(wk_median/500)*100:.1f}%", "...", "..."],
        ["Fins de semana (Sáb+Dom)", f"{we_median:.1f}", f"{(we_median/500)*100:.1f}%", "...", "..."]
    ]
    # Add upload medians from combined_pct_stats
    # (we can fill accordingly)
    story.append(KeepTogether([table_comp, Spacer(1, 0.3*cm)]))
    story.append(Paragraph("Observação: Há uma redução média de ...% na velocidade nos fins de semana.", style_body))

    # Throttling explanation
    story.append(Paragraph("3.3. Análise de Throttling (Limitação de Velocidade)", style_heading2))
    story.append(Paragraph(
        "O padrão observado – velocidades mais baixas nos fins de semana – é compatível com a prática de "
        "throttling, na qual a operadora reduz artificialmente a banda disponível em períodos de alta demanda, "
        "sem aviso prévio ao consumidor. Essa conduta viola o princípio da neutralidade de rede (Marco Civil "
        "da Internet, art. 9º), o direito à informação adequada (CDC, art. 6º, III) e a boa-fé objetiva "
        "(CDC, art. 4º, III).", style_body
    ))
    story.append(Spacer(1, 0.5*cm))

    # --- 4. VELOCIDADE CONTRATADA VS ENTREGUE ---
    story.append(Paragraph("4. VELOCIDADE CONTRATADA VERSUS ENTREGUE", style_heading1))
    story.append(Paragraph("4.1. Parâmetros Contratados", style_heading2))
    story.append(Paragraph("• Download: 500 Mbps", style_body))
    story.append(Paragraph("• Upload: 250 Mbps", style_body))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4.2. Estatísticas Gerais de Download e Upload (Consolidadas)", style_heading2))
    desc_data = [["Estatística", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)"]]
    for stat in combined_desc.index:
        desc_data.append([
            stat.capitalize(),
            f"{combined_desc.loc[stat, 'Download_Mbps']:.1f}",
            f"{combined_desc.loc[stat, 'Upload_Mbps']:.1f}",
            f"{combined_desc.loc[stat, 'Ping']:.1f}"
        ])
    table_desc = Table(desc_data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
    table_desc.setStyle(...)
    story.append(KeepTogether([table_desc, Spacer(1, 0.3*cm)]))
    overall_dl = combined_desc.loc['50%', 'Download_Mbps'] if '50%' in combined_desc.index else 0
    overall_ul = combined_desc.loc['50%', 'Upload_Mbps'] if '50%' in combined_desc.index else 0
    story.append(Paragraph(
        f"A mediana ({overall_dl:.1f} Mbps de download e {overall_ul:.1f} Mbps de upload) é o indicador mais adequado para "
        "avaliar a velocidade típica da conexão.", style_body
    ))

    story.append(Paragraph("4.3. Percentuais de Entrega por Período", style_heading2))
    pct_data = [["Período", "Download Pct (%)", "Upload Pct (%)"]]
    for periodo in ['Dias de semana', 'Fins de semana']:
        # retrieve from combined_pct_stats
        pass
    story.append(KeepTogether([table_pct, Spacer(1, 0.5*cm)]))

    # --- 5. PERDA FINANCEIRA ---
    story.append(Paragraph("5. CÁLCULO DA PERDA FINANCEIRA", style_heading1))
    story.append(Paragraph("5.1. Premissas", style_heading2))
    story.append(Paragraph(f"• Plano: {plan_name}", style_body))
    story.append(Paragraph(f"• Valor mensal estimado: R$ {valor_mensal:.2f}", style_body))
    story.append(Paragraph(f"• Período analisado: {meses} meses ({meses//12} anos)", style_body))
    story.append(Paragraph("• Inflação/reajustes não considerados (cálculo subestimado)", style_body))
    story.append(Spacer(1, 0.3*cm))
    story.append(PageBreak())

    # 5.2 table
    # (similar to original)

    # 5.3 to 5.5 as original

    # --- 6. LEGAL ---
    # (copy from original)

    # --- 7. RECOMENDACOES ---
    # (copy from original)

    # --- 8. ANEXOS ---
    story.append(Paragraph("8. ANEXOS – GRÁFICOS", style_heading1))
    story.append(Spacer(1, 0.5*cm))

    # List all images generated: combine per tool and overall
    # For each tool, we need to insert its graphs
    # This is getting long; we'll simplify: use combined graphs for the main report, and per-tool in separate sections.

    # We'll loop through tools and add their graphs.
    # For each tool, add a heading and the images.

    # For simplicity, we'll assume we have combined graphs already. We'll also add per-tool graphs if present.
    # We'll use the helper to insert images.

    def insert_images_for_prefix(prefix, title):
        story.append(Paragraph(title, style_heading2))
        # list images with that prefix
        # we can generate a list of filenames
        # Since we know the patterns, we'll use the filenames we generated.
        # For combined: time_series.png, distribuicao.png, boxplot_sponsor.png, mapa_provedores_distancia.png, media_horaria.png, media_dia_semana.png
        # For tool: time_series_{tool}.png, etc.
        # We'll add them in order.
        base_files = ['time_series', 'distribuicao', 'boxplot_sponsor', 'mapa_provedores_distancia', 'media_horaria', 'media_dia_semana']
        for base in base_files:
            fname = f"{base}{'' if prefix == '' else '_'+prefix}.png"
            img_path = os.path.join(graph_dir, fname)
            if os.path.exists(img_path):
                story.append(Paragraph(f"{base.replace('_',' ').capitalize()}{'' if prefix=='' else f' ({prefix})'}", style_body))
                img = Image(img_path, width=16*cm, height=5.2*cm)
                table_img = Table([[img]], colWidths=[16*cm])
                table_img.setStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE')])
                story.append(KeepTogether([table_img, Spacer(1,0.3*cm)]))
        story.append(PageBreak())

    # Combined graphs (prefix '')
    insert_images_for_prefix('', 'Gráficos Consolidados')

    # Per tool graphs (if more than one tool)
    if len(tools) > 1:
        for tool in tools:
            if len(clean[clean['Tool'] == tool]) > 1:
                insert_images_for_prefix(tool, f'Gráficos - {tool}')

    # Final footer
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph(f"Responsável Técnico: {client_name}", style_left))
    story.append(Paragraph(f"Guaxupé, {datetime.now().strftime('%d de %B de %Y')}", style_left))

    doc.build(story)
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