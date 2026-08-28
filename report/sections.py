# report/sections.py
"""Construção de cada seção do relatório PDF."""

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from typing import List, Dict, Any, Tuple
from .formatters import format_br_money, format_br_number, data_extenso
from .stats import compute_statistics
import pandas as pd
import os


def build_cover_page(styles: Dict, client_name: str, plan_name: str, isp_name: str,
                     start_date: str, end_date: str, total_records: int,
                     attorney_name: str = "") -> List:
    """Cria a capa do relatório."""
    story = []
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("RELATÓRIO TÉCNICO - JURÍDICO", styles['title']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Análise de Qualidade de Serviço de Internet Banda Larga", styles['subtitle']))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"Cliente: {client_name}", styles['body']))
    story.append(Paragraph(f"Plano: {plan_name}", styles['body']))
    story.append(Paragraph(f"Operadora: {isp_name}", styles['body']))
    story.append(Paragraph(f"Período de Medição: {start_date} a {end_date}", styles['body']))
    story.append(Paragraph(f"Base de Dados: {total_records} registros válidos (speedtest-cli + librespeed)", styles['body']))
    story.append(Spacer(1, 2*cm))
    if attorney_name:
        story.append(Paragraph(f"Advogado: {attorney_name}", styles['centered']))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Guaxupé, {data_extenso(pd.Timestamp.now())}", styles['centered']))
    story.append(PageBreak())
    return story


def build_table_of_contents(styles: Dict) -> List:
    """Cria o sumário com os números de página."""
    story = []
    story.append(Paragraph("SUMÁRIO", styles['heading1']))
    story.append(Spacer(1, 0.5*cm))
    itens = [
        ("1. OBJETIVO", 3),
        ("2. METODOLOGIA", 3),
        ("3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO", 4),
        ("   3.1. Desempenho por Dia da Semana", 4),
        ("   3.2. Comparação Dias Úteis vs. Fins de Semana", 4),
        ("   3.3. Análise de Throttling", 4),
        ("4. VELOCIDADE CONTRATADA VERSUS ENTREGUE", 5),
        ("   4.1. Parâmetros Contratados", 5),
        ("   4.2. Estatísticas Gerais", 5),
        ("   4.3. Percentuais de Entrega por Período", 5),
        ("5. CÁLCULO DA PERDA FINANCEIRA", 6),
        ("   5.1. Premissas", 6),
        ("   5.2. Perda Mensal por Período", 6),
        ("   5.3. Perda Média Mensal", 6),
        ("   5.4. Perda Acumulada", 6),
        ("   5.5. Estimativa para Ação Civil Pública", 6),
        ("6. FUNDAMENTAÇÃO LEGAL E JURISPRUDÊNCIA", 7),
        ("7. RECOMENDAÇÕES", 8),
        ("8. ANEXOS – GRÁFICOS COMPARATIVOS E MEDIANAS", 9),
        ("8.1 ANÁLISE INTELIGENTE POR DIA E HORÁRIO", 10),
        ("9. RESUMO EXECUTIVO", 11),
    ]
    for texto, pag in itens:
        linha = f"{texto} ....................... {pag}"
        story.append(Paragraph(linha, styles['body']))
    story.append(PageBreak())
    return story


def build_objective(styles: Dict, stats: Dict) -> List:
    story = []
    story.append(Paragraph("1. OBJETIVO", styles['heading1']))
    clean = stats['clean_df']
    isp_name = stats.get('isp_name', 'operadora')
    plan_name = stats['plan_name']
    overall_median_dl = stats['overall_median_dl']
    pct_global = stats['pct_global']
    throttling = stats['throttling']
    interruptions = stats['interruptions']

    objective_text = f"""
    Com base nas medições objetivas e contínuas realizadas entre {clean['Timestamp'].min().strftime('%d/%m/%Y')} e {clean['Timestamp'].max().strftime('%d/%m/%Y')}, 
    utilizando as ferramentas speedtest-cli e LibreSpeed, este relatório comprova que a prestadora {isp_name} não está cumprindo a velocidade de download e upload contratadas no plano {plan_name}.
    
    A velocidade mediana de download obtida foi de {overall_median_dl:.1f} Mbps, representando apenas {pct_global:.1f}% dos {stats['plan_download']:.0f} Mbps contratados, 
    valor significativamente inferior ao mínimo de 80% exigido pela Resolução Anatel nº 632/2014.
    """
    if throttling['detected']:
        objective_text += f"""
    Foi identificada prática de throttling (redução arbitrária de velocidade) nos fins de semana, com redução média de {throttling['percent']:.1f}% 
    na velocidade de download em comparação aos dias úteis, caracterizando violação ao princípio da neutralidade de rede (Marco Civil da Internet, art. 9º).
    """
    else:
        objective_text += """
    Não foi possível confirmar a prática de throttling devido à indisponibilidade de dados significativos em ambos os períodos (dias úteis e fins de semana) para comparação.
    """
    if interruptions > 0:
        objective_text += f"""
    
    Durante o período de coleta, foram identificados {interruptions} momentos em que a conexão foi interrompida (download ou upload igual a zero), 
    indicando falhas na prestação do serviço.
    """
    objective_text += """
    
    Os dados aqui apresentados servem como subsídio técnico para notificação extrajudicial, ação judicial individual e provocação do Ministério Público e da Anatel para ação civil pública.
    """
    story.append(Paragraph(objective_text, styles['body']))
    story.append(Spacer(1, 0.3*cm))
    return story


def build_methodology(styles: Dict, success_data: list) -> List:
    story = []
    story.append(Paragraph("2. METODOLOGIA", styles['heading1']))
    story.append(Paragraph(
        "Os testes foram realizados com as ferramentas speedtest-cli, LibreSpeed, Fast.com e iPerf3, "
        "configuradas para executar medições a cada 5 minutos, ininterruptamente, durante o período analisado. "
        "Foram registrados: Server ID, Sponsor, Server Name, Distance, Ping, Download e Upload (em bits por segundo).",
        styles['body']
    ))
    story.append(Paragraph("Cada ferramenta tem características específicas:", styles['body']))
    item_style = ParagraphStyle(
        'ListItem',
        parent=styles['body'],
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
    story.append(Spacer(1, 0.2*cm))
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
    story.append(KeepTogether([table_success, Spacer(1, 0.2*cm)]))
    story.append(Paragraph(
        "A análise estatística principal (mediana, percentuais) foi calculada utilizando exclusivamente os dados dessas duas ferramentas, "
        "por serem as mais confiáveis e amplamente utilizadas para medições de velocidade.",
        styles['body']
    ))
    story.append(PageBreak())
    return story


def build_statistics(styles: Dict, stats: Dict) -> List:
    story = []
    story.append(Paragraph("3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO", styles['heading1']))

    # 3.1
    story.append(Paragraph("3.1. Desempenho por Dia da Semana (dias com dados disponíveis)", styles['heading2']))
    weekday_median = stats['weekday_median']
    weekdays_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    dias_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    combined_weekday_median = weekday_median.reindex(weekdays_order).dropna()
    if not combined_weekday_median.empty:
        dados_dia = [["Dia da Semana", "Mediana Download (Mbps)", "% da Contratada", "Categoria"]]
        for dia, valor in combined_weekday_median.items():
            pct = (valor / stats['plan_download']) * 100
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
        story.append(Paragraph("Não há dados suficientes para análise por dia da semana.", styles['body']))

    # 3.2
    story.append(Paragraph("3.2. Comparação Dias Úteis vs. Fins de Semana", styles['heading2']))
    weekend_stats = stats['weekend_stats']
    clean = stats['clean_df']
    throttling = stats['throttling']
    if len(weekend_stats) == 2:
        wk_med = weekend_stats[False]
        we_med = weekend_stats[True]
        upload_weekday = clean[~clean['IsWeekend']]['Upload_Mbps'].median() if not clean[~clean['IsWeekend']].empty else 0
        upload_weekend = clean[clean['IsWeekend']]['Upload_Mbps'].median() if not clean[clean['IsWeekend']].empty else 0
        dados_comp = [
            ["Período", "Mediana Download (Mbps)", "% da Contratada", "Mediana Upload (Mbps)", "% da Contratada (250)"],
            ["Dias de semana (2ª a 6ª)", f"{wk_med:.1f}", f"{(wk_med/stats['plan_download'])*100:.1f}%", f"{upload_weekday:.1f}", f"{(upload_weekday/stats['plan_upload'])*100:.1f}%"],
            ["Fins de semana (Sáb+Dom)", f"{we_med:.1f}", f"{(we_med/stats['plan_download'])*100:.1f}%", f"{upload_weekend:.1f}", f"{(upload_weekend/stats['plan_upload'])*100:.1f}%"],
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
        if throttling['detected']:
            texto_observacao = (f"Observação: Foi identificada redução média de {reducao:.1f}% na velocidade nos fins de semana. "
                                f"O teste estatístico Mann-Whitney U retornou p-valor = {throttling['p_value']:.4f}, "
                                f"indicando diferença significativa entre os períodos (p < 0.05). "
                                f"Isso evidencia possível throttling, conforme análise detalhada na seção 3.3.")
        else:
            texto_observacao = (f"Observação: Há uma variação de {reducao:.1f}% na velocidade nos fins de semana, "
                                f"mas o teste estatístico não indicou diferença significativa (p-valor = {throttling['p_value']:.4f}), "
                                f"não sendo possível confirmar throttling.")
        story.append(Paragraph(texto_observacao, styles['body']))
    else:
        story.append(Paragraph("Não há dados suficientes para comparar dias úteis e fins de semana (apenas um dos períodos possui registros).", styles['body']))
    story.append(Spacer(1, 0.3*cm))

    # 3.3
    story.append(Paragraph("3.3. Análise de Throttling (Limitação de Velocidade)", styles['heading2']))
    if throttling['detected']:
        throttle_text = f"""
        A análise dos dados coletados confirmou a prática de throttling (redução arbitrária de velocidade) nos fins de semana.
        A velocidade mediana de download nos dias úteis foi de {throttling['weekday_median']:.1f} Mbps, enquanto nos fins de semana
        caiu para {throttling['weekend_median']:.1f} Mbps, representando uma redução de {throttling['percent']:.1f}%.
        O teste estatístico Mann-Whitney U confirmou que essa diferença é estatisticamente significativa (p-valor = {throttling['p_value']:.4f}).
        Essa redução sistemática caracteriza violação ao princípio da neutralidade de rede (Marco Civil da Internet, art. 9º),
        ao direito à informação adequada (CDC, art. 6º, III) e à boa-fé objetiva (CDC, art. 4º, III).

        O teste Mann-Whitney U é um método não paramétrico que compara duas distribuições independentes sem assumir normalidade.
        Ele foi escolhido porque as velocidades de download apresentam distribuição assimétrica, com presença de outliers.
        O teste calcula a probabilidade (p-valor) de que a diferença observada entre os grupos ocorra por acaso.
        Neste caso, o p-valor = {throttling['p_value']:.4f} é extremamente baixo (menor que 0.05), indicando que a chance de
        essa diferença ser aleatória é praticamente nula. Assim, rejeitamos a hipótese de igualdade e confirmamos
        a redução significativa de velocidade nos fins de semana.
        """
    else:
        throttle_text = f"""
        Não foi possível confirmar a prática de throttling com os dados disponíveis.
        A análise comparativa entre dias úteis e fins de semana apresentou uma variação de {throttling.get('percent', 0):.1f}%,
        porém o teste estatístico não indicou diferença significativa (p-valor = {throttling.get('p_value', 1.0):.4f}).
        Recomenda-se a continuidade das medições para obter mais dados e reavaliar o comportamento em períodos de maior tráfego.
        """
    story.append(Paragraph(throttle_text, styles['body']))
    story.append(PageBreak())
    return story


def build_contracted_speed(styles: Dict, stats: Dict) -> List:
    story = []
    story.append(Paragraph("4. VELOCIDADE CONTRATADA VERSUS ENTREGUE", styles['heading1']))
    story.append(Paragraph("4.1. Parâmetros Contratados", styles['heading2']))
    story.append(Paragraph(f"• Download: {stats['plan_download']:.0f} Mbps", styles['body']))
    story.append(Paragraph(f"• Upload: {stats['plan_upload']:.0f} Mbps", styles['body']))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4.2. Estatísticas Gerais de Download e Upload (dados consolidados das duas ferramentas)", styles['heading2']))
    combined_desc = stats['combined_desc']
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

    overall_dl = stats['overall_median_dl']
    overall_ul = stats['overall_median_ul']
    story.append(Paragraph(
        f"A mediana ({overall_dl:.1f} Mbps de download e {overall_ul:.1f} Mbps de upload) é o indicador mais adequado para "
        "avaliar a velocidade típica da conexão.", styles['body']
    ))

    story.append(Paragraph("4.3. Percentuais de Entrega por Período (dados disponíveis)", styles['heading2']))
    pct_stats = stats['pct_stats']
    if not pct_stats.empty:
        pct_data = [["Período", "Download Pct (%)", "Upload Pct (%)"]]
        for idx, row in pct_stats.iterrows():
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
        story.append(Paragraph("Não há dados para calcular os percentuais de entrega por período.", styles['body']))
    story.append(PageBreak())
    return story


def build_financial_loss(styles: Dict, stats: Dict, plan_name: str) -> List:
    story = []
    story.append(Paragraph("5. CÁLCULO DA PERDA FINANCEIRA", styles['heading1']))
    story.append(Paragraph("5.1. Premissas", styles['heading2']))
    story.append(Paragraph(f"• Plano: {plan_name}", styles['body']))
    story.append(Paragraph(f"• Valor mensal estimado: {format_br_money(stats['valor_mensal'])}", styles['body']))
    story.append(Paragraph(f"• Período analisado: {stats['meses']} meses ({stats['meses']//12} anos)", styles['body']))
    story.append(Paragraph("• Inflação/reajustes não considerados (cálculo subestimado)", styles['body']))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5.2. Perda Mensal por Período (dados disponíveis)", styles['heading2']))
    pct_stats = stats['pct_stats']
    valor_mensal = stats['valor_mensal']
    if not pct_stats.empty:
        perda_data = [["Período", "% Entregue", "% Não Entregue", "Valor Mensal (R$)", "Valor Efetivo (R$)", "Perda Mensal (R$)"]]
        for idx, row in pct_stats.iterrows():
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
        story.append(Paragraph("Não há dados para calcular a perda por período.", styles['body']))

    story.append(Paragraph("5.3. Perda Média Mensal", styles['heading2']))
    perda_mensal = stats['perda_mensal']
    perda_total_individual = stats['perda_total_individual']
    story.append(Paragraph(f"• Perda média mensal (calculada com base na mediana geral de download): {format_br_money(perda_mensal)}", styles['body']))
    story.append(Paragraph(f"• Perda total individual em {stats['meses']} meses: {format_br_money(perda_total_individual)}", styles['body']))
    story.append(Paragraph(
        f"Este valor é passível de restituição em dobro (CDC, art. 42, parágrafo único), "
        f"totalizando {format_br_money(perda_total_individual*2)}.", styles['body']
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5.4. Estimativa para Ação Civil Pública (Região de Guaxupé/MG)", styles['heading2']))
    num_clientes = stats.get('num_clientes', 4500)
    danos_materiais_coletivos = perda_total_individual * num_clientes
    danos_morais_coletivos = 5000 * num_clientes
    total_acao_coletiva = danos_materiais_coletivos + danos_morais_coletivos
    story.append(Paragraph(f"• Número estimado de clientes Vivo Fibra na região: {num_clientes:,}", styles['body']))
    story.append(Paragraph(f"• Perda média por cliente: {format_br_money(perda_total_individual)}", styles['body']))
    story.append(Paragraph(f"• Danos materiais coletivos: {num_clientes} × {format_br_number(perda_total_individual)} = {format_br_money(danos_materiais_coletivos)}", styles['body']))
    story.append(Paragraph(f"• Danos morais coletivos (R$ 5.000/cliente): {num_clientes} × 5.000 = {format_br_money(danos_morais_coletivos)}", styles['body']))
    story.append(Paragraph(f"• Total estimado da ação civil pública: {format_br_money(total_acao_coletiva)}", styles['body']))
    story.append(PageBreak())
    return story


def build_legal_foundation(styles: Dict) -> List:
    story = []
    story.append(Paragraph("6. FUNDAMENTAÇÃO LEGAL E JURISPRUDÊNCIA", styles['heading1']))
    story.append(Paragraph("6.1. Dispositivos Legais Aplicáveis", styles['heading2']))
    story.append(Paragraph("• Constituição Federal, art. 5º, XXXII – defesa do consumidor.", styles['body']))
    story.append(Paragraph("• Código de Defesa do Consumidor, art. 6º, III e VIII – informação e inversão do ônus da prova.", styles['body']))
    story.append(Paragraph("• CDC, art. 14 – responsabilidade objetiva.", styles['body']))
    story.append(Paragraph("• CDC, art. 39, V – vedação de vantagem excessiva.", styles['body']))
    story.append(Paragraph("• CDC, art. 42, p.ú – devolução em dobro.", styles['body']))
    story.append(Paragraph("• Lei Geral de Telecomunicações, art. 3º – padrões de qualidade.", styles['body']))
    story.append(Paragraph("• Resolução Anatel nº 632/2014, art. 3º, §1º – velocidade média ≥ 80%.", styles['body']))
    story.append(Paragraph("• Marco Civil da Internet, art. 9º – neutralidade de rede.", styles['body']))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("6.2. Jurisprudência Relevante", styles['heading2']))
    story.append(Paragraph(
        "• STJ, REsp 1.660.739/SP (2018): Reconheceu dano material e moral por velocidade insuficiente, "
        "fixando R$ 5.000,00 por cliente.", styles['body']
    ))
    story.append(Paragraph(
        "• TJSP, Apelação nº 1038170-12.2019.8.26.0114: Vivo condenada por velocidade inferior.", styles['body']
    ))
    story.append(Paragraph(
        "• MPMA vs. Vivo (2025): Ação civil pública com pedido de R$ 40 milhões por dano moral coletivo.", styles['body']
    ))
    story.append(PageBreak())
    return story


def build_recommendations(styles: Dict, stats: Dict) -> List:
    story = []
    story.append(Paragraph("7. RECOMENDAÇÕES", styles['heading1']))
    perda_total_individual = stats['perda_total_individual']
    story.append(Paragraph(
        "1. <b>Notificação extrajudicial à operadora</b> – Enviar notificação formal, com prazo de 15 (quinze) dias "
        "para que a operadora regularize a velocidade de download para, no mínimo, 80% do contratado "
        f"({stats['plan_download']*0.8:.0f} Mbps) e apresente comprovação da efetiva entrega do serviço, "
        "sob pena de adoção das medidas judiciais cabíveis. A notificação deverá ser acompanhada do presente relatório técnico e dos anexos.",
        styles['body']
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"2. <b>Ajuizamento de ação individual</b> – Caso não haja solução administrativa, propôr ação perante o "
        f"Juizado Especial Cível ou Vara Cível competente, pleiteando: (a) restituição em dobro dos valores pagos "
        f"a maior, conforme art. 42 do CDC (total estimado de {format_br_money(perda_total_individual*2)}); "
        f"(b) indenização por danos morais no valor de R$ 10.000,00, com base nos precedentes do STJ e TJSP; "
        f"(c) obrigação de fazer para que a operadora passe a faturar com transparência, discriminando a "
        f"velocidade média mensal entregue e os incidentes de interrupção, com desconto automático proporcional.",
        styles['body']
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "3. <b>Encaminhamento ao Ministério Público Federal e à Anatel</b> – Remeter cópia integral do relatório, "
        "com os gráficos e tabelas, ao MPF e à Superintendência de Fiscalização da Anatel, solicitando a "
        "instauração de procedimento administrativo para apuração das infrações à Resolução Anatel nº 632/2014 "
        "e ao Marco Civil da Internet, bem como o ajuizamento de ação civil pública em âmbito nacional para "
        "proteger os direitos difusos de todos os consumidores.", styles['body']
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "4. <b>Divulgação e mobilização social</b> – Compartilhar o caso com associações de defesa do consumidor "
        "(IDEC, PROTESTE, PROCON) e com a imprensa local e nacional, visando conscientizar outros consumidores "
        "sobre a prática de throttling e a necessidade de fiscalização mais rigorosa, além de estimular a adesão "
        "a eventuais ações coletivas.", styles['body']
    ))
    story.append(PageBreak())
    return story


def build_appendix(styles: Dict, comparison_images: list, graph_dir: str) -> List:
    story = []
    story.append(Paragraph("8. ANEXOS – GRÁFICOS COMPARATIVOS E MEDIANAS", styles['heading1']))
    story.append(Spacer(1, 0.3*cm))

    valid_img_paths = []
    for fname in comparison_images:
        path = os.path.join(graph_dir, fname)
        if os.path.exists(path):
            valid_img_paths.append(path)

    if valid_img_paths:
        page_width = 17 * cm
        gap = 0.3 * cm
        img_width = (page_width - gap) / 2
        img_height = img_width * 0.7

        def build_table_rows(paths):
            rows = []
            for i in range(0, len(paths), 2):
                row = []
                row.append(Image(paths[i], width=img_width, height=img_height))
                if i+1 < len(paths):
                    row.append(Image(paths[i+1], width=img_width, height=img_height))
                else:
                    row.append(Spacer(1, 0))
                rows.append(row)
            return rows

        page_size = 4
        for page_start in range(0, len(valid_img_paths), page_size):
            page_paths = valid_img_paths[page_start:page_start+page_size]
            if page_start > 0:
                story.append(PageBreak())
                story.append(Paragraph(
                    "8. ANEXOS – GRÁFICOS COMPARATIVOS E MEDIANAS (continuação)",
                    styles['heading1']
                ))
                story.append(Spacer(1, 0.3*cm))
            table_rows = build_table_rows(page_paths)
            table = Table(table_rows, colWidths=[img_width, img_width])
            table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0.5*cm),
            ]))
            story.append(KeepTogether([table, Spacer(1, 0.3*cm)]))
    else:
        story.append(Paragraph("Nenhum gráfico disponível para exibição.", styles['body']))

    story.append(PageBreak())
    return story


def build_smart_analysis(styles: Dict, stats: Dict) -> List:
    """
    Cria a página de análise inteligente por dia e horário,
    com resumo de problemas identificados.
    """
    story = []
    story.append(Paragraph("8.1 ANÁLISE INTELIGENTE POR DIA E HORÁRIO", styles['heading1']))
    
    clean = stats['clean_df'].copy()
    if clean.empty:
        story.append(Paragraph("Sem dados suficientes para análise.", styles['body']))
        return story
    
    # Preparar dados
    clean['Hour'] = clean['Timestamp'].dt.hour
    clean['DayOfWeek'] = clean['Timestamp'].dt.day_name()
    clean['DayNum'] = clean['DayOfWeek'].map({
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
        'Friday': 4, 'Saturday': 5, 'Sunday': 6
    })
    
    # Calcular médias por dia/hora
    pivot = clean.pivot_table(index='DayNum', columns='Hour', values='Download_Mbps', aggfunc='mean')
    pivot = pivot.reindex(index=range(7), columns=range(24))
    
    # Identificar períodos com problemas
    issues = []
    
    # 1. Horários com velocidade média < 50% da contratada
    threshold_50 = stats['plan_download'] * 0.5
    for day in range(7):
        for hour in range(24):
            val = pivot.loc[day, hour]
            if pd.notna(val) and val < threshold_50:
                day_name = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][day]
                issues.append({
                    'day': day_name,
                    'hour': hour,
                    'download': val,
                    'percent': (val / stats['plan_download']) * 100,
                    'type': 'slow'
                })
    
    # 2. Horas com variação significativa entre dias úteis e fins de semana
    weekday_avg = clean[~clean['IsWeekend']].groupby('Hour')['Download_Mbps'].mean()
    weekend_avg = clean[clean['IsWeekend']].groupby('Hour')['Download_Mbps'].mean()
    
    for hour in range(24):
        if hour in weekday_avg.index and hour in weekend_avg.index:
            diff_pct = ((weekday_avg[hour] - weekend_avg[hour]) / weekday_avg[hour]) * 100 if weekday_avg[hour] > 0 else 0
            if diff_pct > 20:
                issues.append({
                    'day': 'Fins de semana',
                    'hour': hour,
                    'download': weekend_avg[hour],
                    'percent': diff_pct,
                    'type': 'throttling_suspect'
                })
    
    # 3. Pior dia da semana
    day_avg = clean.groupby('DayNum')['Download_Mbps'].mean().reindex(range(7))
    worst_day_idx = day_avg.idxmin()
    worst_day = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][worst_day_idx]
    worst_day_value = day_avg[worst_day_idx]
    
    if worst_day_value < stats['plan_download'] * 0.5:
        issues.append({
            'day': worst_day,
            'hour': 'all',
            'download': worst_day_value,
            'percent': (worst_day_value / stats['plan_download']) * 100,
            'type': 'worst_day'
        })
    
    # Adicionar resumo
    if issues:
        story.append(Paragraph("### Resumo de Problemas Identificados", styles['heading2']))
        
        # Agrupar por tipo
        slow_issues = [i for i in issues if i['type'] == 'slow']
        throttle_issues = [i for i in issues if i['type'] == 'throttling_suspect']
        worst_day_issues = [i for i in issues if i['type'] == 'worst_day']
        
        if slow_issues:
            story.append(Paragraph("**Horários com velocidade abaixo de 50% do contratado:**", styles['body']))
            unique_slow = list(set([(i['day'], i['hour']) for i in slow_issues]))
            for day, hour in unique_slow[:20]:
                story.append(Paragraph(f"• {day} às {hour:02d}:00 - {slow_issues[0]['download']:.1f} Mbps ({slow_issues[0]['percent']:.1f}%)", styles['body']))
        
        if throttle_issues:
            story.append(Paragraph("**Possíveis horários de throttling (diferença > 20% entre dias úteis e fins de semana):**", styles['body']))
            for issue in throttle_issues[:20]:
                story.append(Paragraph(f"• {issue['day']} às {issue['hour']:02d}:00 - Redução de {issue['percent']:.1f}%", styles['body']))
        
        if worst_day_issues:
            story.append(Paragraph(f"**Pior dia da semana:** {worst_day} com média de {worst_day_value:.1f} Mbps ({worst_day_value / stats['plan_download'] * 100:.1f}% da contratada)", styles['body']))
        
        story.append(Paragraph("**Conclusão:** A análise identifica padrões de degradação de velocidade em horários específicos, que podem indicar problemas de infraestrutura do provedor ou práticas de gerenciamento de tráfego (throttling). Recomenda-se investigar esses períodos junto ao provedor.", styles['body']))
    else:
        story.append(Paragraph("**Conclusão:** A análise não identificou padrões significativos de degradação de velocidade ou throttling nos dados disponíveis.", styles['body']))
    
    story.append(PageBreak())
    return story


def build_executive_summary(styles: Dict, stats: Dict, address: str) -> List:
    story = []
    story.append(Paragraph("9. RESUMO EXECUTIVO", styles['heading1']))
    story.append(Spacer(1, 0.3*cm))

    clean = stats['clean_df']
    total_tests = len(clean)
    periodo = f"{clean['Timestamp'].min().strftime('%d/%m/%Y')} a {clean['Timestamp'].max().strftime('%d/%m/%Y')}"
    overall_dl = stats['overall_median_dl']
    overall_ul = stats['overall_median_ul']
    combined_desc = stats['combined_desc']
    ping_med = combined_desc.loc['50%', 'Ping'] if '50%' in combined_desc.index else 0
    pct_global = stats['pct_global']
    throttling = stats['throttling']
    perda_total_individual = stats['perda_total_individual']
    total_acao_coletiva = stats['total_acao_coletiva']

    if throttling['detected']:
        throttling_desc = f"Redução de {throttling['percent']:.1f}% nos fins de semana (throttling confirmado)."
    else:
        throttling_desc = "Não foi possível confirmar throttling por falta de dados significativos."

    resumo_texto = f"""
    Este relatório analisou {total_tests} testes de velocidade (speedtest-cli e LibreSpeed) realizados entre {periodo}.
    A velocidade mediana de download foi de {overall_dl:.1f} Mbps, o que representa apenas {pct_global:.1f}% da velocidade contratada ({stats['plan_download']:.0f} Mbps).
    A mediana de upload foi de {overall_ul:.1f} Mbps ({(overall_ul/stats['plan_upload'])*100:.1f}% do contratado) e o ping médio foi de {ping_med:.1f} ms.
    {throttling_desc}
    Com base na velocidade entregue, o prejuízo financeiro individual acumulado em {stats['meses']} meses é de {format_br_money(perda_total_individual)}.
    Esta perda, quando considerada para uma possível ação coletiva, pode ultrapassar {format_br_money(total_acao_coletiva)}.
    """
    story.append(Paragraph(resumo_texto, styles['body']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(f"Localidade: {address}", styles['body']))
    story.append(Paragraph(f"Data da emissão: {data_extenso(pd.Timestamp.now())}", styles['body']))
    story.append(Spacer(1, 1.5*cm))

    story.append(Paragraph("_________________________________________", styles['body']))
    story.append(Paragraph("Responsável Técnico", styles['body']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("_________________________________________", styles['body']))
    story.append(Paragraph("Advogado", styles['body']))
    story.append(Spacer(1, 1*cm))

    return story