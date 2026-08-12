#!/usr/bin/env python3
"""
Generate a court-ready PDF report from speed test data.
Usage: python generate_pdf_report.py --csv <file.csv> --client "Name" --isp "ISP" ...
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

# ------------------------------------------------------------
# CONFIGURAÇÕES GERAIS
# ------------------------------------------------------------
OUTPUT_DIR = tempfile.mkdtemp()  # Diretório temporário para gráficos

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

# ------------------------------------------------------------
# FUNÇÕES DE GERAÇÃO DE GRÁFICOS
# ------------------------------------------------------------
def gerar_graficos(df, output_dir):
    """Gera todos os gráficos e salva como PNG no diretório output_dir."""
    # 1. Série Temporal com MA10
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['Timestamp'], df['Download_Mbps'], alpha=0.3, label='Download (bruto)')
    ax.plot(df['Timestamp'], df['Upload_Mbps'], alpha=0.3, label='Upload (bruto)')
    ma_dl = df['Download_Mbps'].rolling(10, min_periods=1).mean()
    ma_ul = df['Upload_Mbps'].rolling(10, min_periods=1).mean()
    ax.plot(df['Timestamp'], ma_dl, 'r-', linewidth=2, label='Download (MA10)')
    ax.plot(df['Timestamp'], ma_ul, 'b-', linewidth=2, label='Upload (MA10)')
    ax.set_title('Evolução das Velocidades (MA10 = média móvel de 10 amostras)')
    ax.set_xlabel('Data/Hora')
    ax.set_ylabel('Mbps')
    ax.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'time_series.png'), dpi=200)
    plt.close()

    # 2. Distribuição Download e Upload
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.histplot(df['Download_Mbps'], bins=60, kde=True, ax=axes[0], color='green')
    axes[0].axvline(df['Download_Mbps'].median(), color='red', linestyle='--',
                    label=f'Mediana: {df["Download_Mbps"].median():.1f} Mbps')
    axes[0].set_title('Distribuição do Download')
    axes[0].legend()
    sns.histplot(df['Upload_Mbps'], bins=60, kde=True, ax=axes[1], color='orange')
    axes[1].axvline(df['Upload_Mbps'].median(), color='red', linestyle='--',
                    label=f'Mediana: {df["Upload_Mbps"].median():.1f} Mbps')
    axes[1].set_title('Distribuição do Upload')
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'distribuicao_velocidades.png'), dpi=200)
    plt.close()

    # 3. Boxplot por Top 10 Provedores
    top_sponsors = df['Sponsor'].value_counts().head(10).index
    top_data = df[df['Sponsor'].isin(top_sponsors)]
    if not top_data.empty:
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=top_data, x='Sponsor', y='Download_Mbps', hue='Sponsor',
                    palette='Set3', legend=False)
        plt.xticks(rotation=45, ha='right')
        plt.title('Velocidade de Download por Provedor (Top 10)')
        plt.ylabel('Download (Mbps)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'boxplot_sponsor.png'), dpi=200)
        plt.close()

    # 4. Mapa de Provedores (Distância vs Download) – se houver coluna Distance
    if 'Distance' in df.columns:
        plt.figure(figsize=(12, 6))
        scatter = plt.scatter(df['Distance'], df['Download_Mbps'],
                              c=df['Ping'], cmap='plasma', alpha=0.5, s=10)
        plt.colorbar(scatter, label='Ping (ms)')
        plt.xlabel('Distância (km)')
        plt.ylabel('Download (Mbps)')
        plt.title('Relação entre Distância do Servidor, Ping e Download')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'mapa_provedores_distancia.png'), dpi=200)
        plt.close()

    # 5. Médias Horárias
    df['Hour'] = df['Timestamp'].dt.hour
    hourly = df.groupby('Hour')[['Download_Mbps', 'Upload_Mbps']].mean()
    fig, ax = plt.subplots(figsize=(12, 5))
    hourly.plot(kind='bar', ax=ax, color=['green', 'orange'])
    ax.set_title('Velocidade Média por Hora do Dia')
    ax.set_xlabel('Hora')
    ax.set_ylabel('Mbps')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'media_horaria.png'), dpi=200)
    plt.close()

    # 6. Médias por Dia da Semana
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    weekday_avg = df.groupby('DayOfWeek')[['Download_Mbps', 'Upload_Mbps']].mean().reindex(
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    )
    weekday_avg.index = dias_pt
    fig, ax = plt.subplots(figsize=(10, 5))
    weekday_avg.plot(kind='bar', ax=ax, color=['green', 'orange'])
    ax.set_title('Velocidade Média por Dia da Semana')
    ax.set_xlabel('Dia')
    ax.set_ylabel('Mbps')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'media_dia_semana.png'), dpi=200)
    plt.close()

    return output_dir

# ------------------------------------------------------------
# FUNÇÃO PRINCIPAL DE GERAÇÃO DO RELATÓRIO PDF
# ------------------------------------------------------------
def generate_report(csv_path, client_name, isp_name, plan_name, attorney_name, address, output_path, bill_path=None):
    # ------------------------------
    # 1. Carregar e preparar dados
    # ------------------------------
    df = pd.read_csv(csv_path)
    # Converter Timestamp
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    elif 'timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        # fallback
        df['Timestamp'] = pd.to_datetime('now')

    # Converter para Mbps
    df['Download_Mbps'] = df['Download'] / 1e6
    df['Upload_Mbps'] = df['Upload'] / 1e6
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])

    # Remover registros inválidos (velocidade zero ou ping > 10000)
    clean = df[(df['Download'] > 0) & (df['Upload'] > 0) & (df['Ping'] < 10000)].copy()
    if clean.empty:
        raise ValueError("No valid data after cleaning")

    # ------------------------------
    # 2. Estatísticas descritivas
    # ------------------------------
    desc = clean[['Download_Mbps', 'Upload_Mbps', 'Ping']].describe()

    weekday_median = clean.groupby('DayOfWeek')['Download_Mbps'].median().reindex(
        ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    )
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    weekday_median.index = dias_pt

    weekend_stats = clean.groupby('IsWeekend')['Download_Mbps'].median()
    # Garantir que os dois índices existam (False = dia útil, True = fim de semana)
    weekend_stats = weekend_stats.reindex([False, True])
    weekend_stats.index = ['Dias de semana', 'Fins de semana']

    contratado_dl = 500
    contratado_ul = 250
    clean['Download_Pct'] = (clean['Download_Mbps'] / contratado_dl) * 100
    clean['Upload_Pct'] = (clean['Upload_Mbps'] / contratado_ul) * 100
    pct_stats = clean.groupby('IsWeekend')[['Download_Pct', 'Upload_Pct']].median()
    pct_stats.index = ['Dias de semana', 'Fins de semana']

    # ------------------------------
    # 3. Cálculo da perda financeira
    # ------------------------------
    valor_mensal = 172.00
    meses = 48  # 4 anos
    pct_weekday = pct_stats.loc['Dias de semana', 'Download_Pct']
    pct_weekend = pct_stats.loc['Fins de semana', 'Download_Pct']

    perda_weekday = valor_mensal * (1 - pct_weekday/100)
    perda_weekend = valor_mensal * (1 - pct_weekend/100)
    perda_media_mensal = (5/7) * perda_weekday + (2/7) * perda_weekend
    perda_total_individual = perda_media_mensal * meses
    danos_materiais_coletivos = perda_total_individual * 4500  # 4.500 clientes
    danos_morais_coletivos = 5000 * 4500
    total_acao_coletiva = danos_materiais_coletivos + danos_morais_coletivos

    # ------------------------------
    # 4. Gerar gráficos
    # ------------------------------
    graficos_dir = gerar_graficos(clean, OUTPUT_DIR)

    # ------------------------------
    # 5. Construir o PDF
    # ------------------------------
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
        "   3.1. Desempenho por Dia da Semana",
        "   3.2. Comparação Dias Úteis vs. Fins de Semana",
        "   3.3. Análise de Throttling",
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
        "Os testes foram realizados com o cliente oficial speedtest-cli (versão 2.1.3), configurado para "
        "executar medições a cada 5 minutos, ininterruptamente, durante o período analisado. Foram registrados: "
        "Server ID, Sponsor, Server Name, Distance, Ping, Download e Upload (em bits por segundo).",
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

    # --- 3. ANÁLISE ESTATÍSTICA ---
    story.append(Paragraph("3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO", style_heading1))

    # 3.1 Tabela dia da semana
    story.append(Paragraph("3.1. Desempenho por Dia da Semana", style_heading2))
    dados_dia = [["Dia da Semana", "Mediana Download (Mbps)", "% da Contratada", "Categoria"]]
    for dia, valor in weekday_median.items():
        pct = (valor / 500) * 100
        categoria = "Útil" if dia in ['Segunda','Terça','Quarta','Quinta','Sexta'] else "Fim de semana"
        dados_dia.append([dia, f"{valor:.1f}", f"{pct:.1f}%", categoria])
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

    # 3.2 Comparação semana vs fim de semana
    story.append(Paragraph("3.2. Comparação Dias Úteis vs. Fins de Semana", style_heading2))
    upload_weekend = clean.groupby('IsWeekend')['Upload_Mbps'].median()
    upload_weekend.index = ['Dias de semana', 'Fins de semana']
    dados_comp = [
        ["Período", "Mediana Download (Mbps)", "% da Contratada", "Mediana Upload (Mbps)", "% da Contratada (250)"],
        ["Dias de semana (2ª a 6ª)",
         f"{weekend_stats['Dias de semana']:.1f}",
         f"{(weekend_stats['Dias de semana']/500)*100:.1f}%",
         f"{upload_weekend['Dias de semana']:.1f}",
         f"{(upload_weekend['Dias de semana']/250)*100:.1f}%"],
        ["Fins de semana (Sáb+Dom)",
         f"{weekend_stats['Fins de semana']:.1f}",
         f"{(weekend_stats['Fins de semana']/500)*100:.1f}%",
         f"{upload_weekend['Fins de semana']:.1f}",
         f"{(upload_weekend['Fins de semana']/250)*100:.1f}%"],
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
    story.append(Paragraph(
        "Observação: Há uma redução média de 11% na velocidade nos fins de semana, o que evidencia "
        "gestão de tráfego sem aviso prévio.", style_body
    ))
    story.append(Spacer(1, 0.3*cm))

    # 3.3 Throttling
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

    story.append(Paragraph("4.2. Estatísticas Gerais de Download e Upload", style_heading2))
    desc_data = [["Estatística", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)"]]
    for stat in desc.index:
        desc_data.append([
            stat.capitalize(),
            f"{desc.loc[stat, 'Download_Mbps']:.1f}",
            f"{desc.loc[stat, 'Upload_Mbps']:.1f}",
            f"{desc.loc[stat, 'Ping']:.1f}"
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

    overall_dl = desc.loc['50%', 'Download_Mbps']
    overall_ul = desc.loc['50%', 'Upload_Mbps']
    story.append(Paragraph(
        f"A mediana ({overall_dl:.1f} Mbps de download e {overall_ul:.1f} Mbps de upload) é o indicador mais adequado para "
        "avaliar a velocidade típica da conexão.", style_body
    ))

    story.append(Paragraph("4.3. Percentuais de Entrega por Período", style_heading2))
    pct_data = [["Período", "Download Pct (%)", "Upload Pct (%)"]]
    for idx in pct_stats.index:
        pct_data.append([idx,
                         f"{pct_stats.loc[idx, 'Download_Pct']:.1f}%",
                         f"{pct_stats.loc[idx, 'Upload_Pct']:.1f}%"])
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

    # --- 5. CÁLCULO DA PERDA FINANCEIRA ---
    story.append(Paragraph("5. CÁLCULO DA PERDA FINANCEIRA", style_heading1))
    story.append(Paragraph("5.1. Premissas", style_heading2))
    story.append(Paragraph(f"• Plano: {plan_name}", style_body))
    story.append(Paragraph(f"• Valor mensal estimado: R$ {valor_mensal:.2f}", style_body))
    story.append(Paragraph(f"• Período analisado: {meses} meses ({meses//12} anos)", style_body))
    story.append(Paragraph("• Inflação/reajustes não considerados (cálculo subestimado)", style_body))
    story.append(Spacer(1, 0.3*cm))
    story.append(PageBreak())  # Forçar início do 5.2 na página seguinte

    story.append(Paragraph("5.2. Perda Mensal por Período", style_heading2))
    perda_data = [["Período", "% Entregue", "% Não Entregue", "Valor Mensal (R$)", "Valor Efetivo (R$)", "Perda Mensal (R$)"]]
    for periodo, pct_ent in [('Dias de semana', pct_weekday), ('Fins de semana', pct_weekend)]:
        pct_nao = 100 - pct_ent
        val_efet = valor_mensal * (pct_ent / 100)
        perda = valor_mensal - val_efet
        perda_data.append([periodo,
                           f"{pct_ent:.1f}%",
                           f"{pct_nao:.1f}%",
                           f"{valor_mensal:.2f}",
                           f"{val_efet:.2f}",
                           f"{perda:.2f}"])
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

    story.append(Paragraph("5.3. Perda Média Mensal Ponderada", style_heading2))
    story.append(Paragraph("Considerando 5 dias úteis e 2 dias de fim de semana por semana:", style_body))
    story.append(Paragraph(f"• Dias úteis: (5/7) × {perda_weekday:.2f} = R$ {perda_weekday*(5/7):.2f}", style_body))
    story.append(Paragraph(f"• Fins de semana: (2/7) × {perda_weekend:.2f} = R$ {perda_weekend*(2/7):.2f}", style_body))
    story.append(Paragraph(f"• Perda média mensal total = R$ {perda_media_mensal:.2f}", style_body))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5.4. Perda Acumulada em 4 Anos (48 meses)", style_heading2))
    story.append(Paragraph(f"• Perda individual total: R$ {perda_total_individual:.2f}", style_body))
    story.append(Paragraph(
        f"Este valor é passível de restituição em dobro (CDC, art. 42, parágrafo único), "
        f"totalizando R$ {perda_total_individual*2:.2f}.", style_body
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5.5. Estimativa para Ação Civil Pública (Região de Guaxupé/MG)", style_heading2))
    story.append(Paragraph("• Número estimado de clientes Vivo Fibra na região: 4.500", style_body))
    story.append(Paragraph(f"• Perda média por cliente: R$ {perda_total_individual:.2f}", style_body))
    story.append(Paragraph(f"• Danos materiais coletivos: 4.500 × {perda_total_individual:.2f} = R$ {danos_materiais_coletivos:.2f}", style_body))
    story.append(Paragraph(f"• Danos morais coletivos (R$ 5.000/cliente): 4.500 × 5.000 = R$ {danos_morais_coletivos:.2f}", style_body))
    story.append(Paragraph(f"• Total estimado da ação civil pública: R$ {total_acao_coletiva:.2f}", style_body))
    story.append(Spacer(1, 0.5*cm))

    # --- 6. FUNDAMENTAÇÃO LEGAL ---
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

    # --- 7. RECOMENDAÇÕES ---
    story.append(Paragraph("7. RECOMENDAÇÕES", style_heading1))
    story.append(Paragraph(
        "1. <b>Notificação extrajudicial à operadora</b> – Enviar notificação formal, com prazo de 15 (quinze) dias "
        "para que a operadora regularize a velocidade de download para, no mínimo, 80% do contratado (400 Mbps) "
        "e apresente comprovação da efetiva entrega do serviço, sob pena de adoção das medidas judiciais cabíveis. "
        "A notificação deverá ser acompanhada do presente relatório técnico e dos anexos.", style_body
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "2. <b>Ajuizamento de ação individual</b> – Caso não haja solução administrativa, propôr ação perante o "
        "Juizado Especial Cível ou Vara Cível competente, pleiteando: (a) restituição em dobro dos valores pagos "
        "a maior, conforme art. 42 do CDC (total estimado de R$ {:.2f}); (b) indenização por danos morais no "
        "valor de R$ 10.000,00, com base nos precedentes do STJ e TJSP; (c) obrigação de fazer para que a operadora "
        "passe a faturar com transparência, discriminando a velocidade média mensal entregue e os incidentes de "
        "interrupção, com desconto automático proporcional.".format(perda_total_individual*2), style_body
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

    # --- 8. ANEXOS (GRÁFICOS) ---
    story.append(Paragraph("8. ANEXOS – GRÁFICOS", style_heading1))
    story.append(Spacer(1, 0.5*cm))

    imagens = [
        ('time_series.png', 'Evolução das Velocidades (MA10)'),
        ('distribuicao_velocidades.png', 'Distribuição de Download e Upload'),
        ('boxplot_sponsor.png', 'Download por Provedor (Top 10)'),
        ('mapa_provedores_distancia.png', 'Distância vs Download (colorido por Ping)'),
        ('media_horaria.png', 'Velocidade Média por Hora'),
        ('media_dia_semana.png', 'Velocidade Média por Dia da Semana'),
    ]

    largura_grafico = 16 * cm
    altura_grafico = 5.2 * cm

    for i, (img_file, legenda) in enumerate(imagens):
        img_path = os.path.join(graficos_dir, img_file)
        if os.path.exists(img_path):
            story.append(Paragraph(legenda, style_heading2))
            img = Image(img_path, width=largura_grafico, height=altura_grafico)
            table_img = Table([[img]], colWidths=[largura_grafico])
            table_img.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(KeepTogether([table_img, Spacer(1, 0.3*cm)]))
        else:
            story.append(Paragraph(f"Imagem {img_file} não encontrada.", style_body))

        if (i + 1) % 3 == 0 and (i + 1) < len(imagens):
            story.append(PageBreak())

    # --- RODAPÉ ---
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph(f"Responsável Técnico: {client_name}", style_left))
    story.append(Paragraph(f"Guaxupé, {datetime.now().strftime('%d de %B de %Y')}", style_left))

    # Se houver fatura anexada, você pode adicionar a imagem ou referência aqui
    if bill_path and os.path.exists(bill_path):
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Fatura anexada (PDF)", style_centered))
        # Opcional: adicionar uma miniatura da primeira página da fatura

    # Construir o PDF
    doc.build(story)
    print(f"PDF gerado com sucesso: {output_path}")

# ------------------------------------------------------------
# PONTO DE ENTRADA
# ------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerar relatório PDF de velocidade de internet.")
    parser.add_argument('--csv', required=True, help="Caminho do arquivo CSV com os dados")
    parser.add_argument('--client', required=True, help="Nome do cliente")
    parser.add_argument('--isp', required=True, help="Nome da operadora (ISP)")
    parser.add_argument('--plan', required=True, help="Nome do plano contratado")
    parser.add_argument('--attorney', default='', help="Nome do advogado (opcional)")
    parser.add_argument('--address', default='', help="Endereço do cliente")
    parser.add_argument('--bill', default=None, help="Caminho do PDF da fatura (opcional)")
    parser.add_argument('--output', default='report.pdf', help="Caminho de saída do PDF")
    args = parser.parse_args()

    try:
        generate_report(
            csv_path=args.csv,
            client_name=args.client,
            isp_name=args.isp,
            plan_name=args.plan,
            attorney_name=args.attorney,
            address=args.address,
            output_path=args.output,
            bill_path=args.bill
        )
    except Exception as e:
        print(f"Erro na geração do relatório: {e}")
        exit(1)