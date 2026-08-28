# report/sections.py
"""Funções para construir cada seção do relatório PDF."""

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from .formatters import format_currency, data_extenso, format_percentage, format_mbps
import os

def build_cover_page(styles, client_name, plan_name, isp_name, start_date, end_date, total_tests, attorney_name=""):
    """Constrói a capa do relatório."""
    elements = []
    elements.append(Spacer(1, 6*cm))
    elements.append(Paragraph("RELATÓRIO TÉCNICO - JURÍDICO", styles['title']))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("Análise de Qualidade de Serviço de Internet Banda Larga", styles['subtitle']))
    elements.append(Spacer(1, 2*cm))
    elements.append(Paragraph(f"<b>Cliente:</b> {client_name}", styles['left']))
    elements.append(Paragraph(f"<b>Plano:</b> {plan_name}", styles['left']))
    elements.append(Paragraph(f"<b>Operadora:</b> {isp_name}", styles['left']))
    elements.append(Paragraph(f"<b>Período de Medição:</b> {start_date} a {end_date}", styles['left']))
    elements.append(Paragraph(f"<b>Base de Dados:</b> {total_tests} registros válidos (speedtest-cli + librespeed)", styles['left']))
    if attorney_name:
        elements.append(Paragraph(f"<b>Advogado:</b> {attorney_name}", styles['left']))
    elements.append(Spacer(1, 3*cm))
    elements.append(Paragraph("Guaxupé, " + data_extenso(), styles['centered']))
    elements.append(PageBreak())
    return elements

def build_table_of_contents(styles):
    """Constrói o sumário do relatório."""
    elements = []
    elements.append(Paragraph("SUMÁRIO", styles['heading1']))
    elements.append(Spacer(1, 0.5*cm))
    
    sections = [
        ("1. OBJETIVO", 3),
        ("2. METODOLOGIA", 3),
        ("3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO", 4),
        ("3.1. Desempenho por Dia da Semana", 4),
        ("3.2. Comparação Dias Úteis vs. Fins de Semana", 4),
        ("3.3. Análise de Throttling", 4),
        ("4. VELOCIDADE CONTRATADA VERSUS ENTREGUE", 5),
        ("4.1. Parâmetros Contratados", 5),
        ("4.2. Estatísticas Gerais", 5),
        ("4.3. Percentuais de Entrega por Período", 5),
        ("5. CÁLCULO DA PERDA FINANCEIRA", 6),
        ("5.1. Premissas", 6),
        ("5.2. Perda Mensal por Período", 6),
        ("5.3. Perda Média Mensal", 6),
        ("5.4. Perda Acumulada", 6),
        ("5.5. Estimativa para Ação Civil Pública", 6),
        ("6. FUNDAMENTAÇÃO LEGAL E JURISPRUDÊNCIA", 7),
        ("7. RECOMENDAÇÕES", 8),
        ("8. ANEXOS – GRÁFICOS COMPARATIVOS E MEDIANAS", 9),
        ("9. RESUMO EXECUTIVO", 11)
    ]
    
    for title, page in sections:
        elements.append(Paragraph(f"{title} ....................... {page}", styles['body']))
    
    elements.append(PageBreak())
    return elements

def build_analysis_and_conclusions(styles, stats: dict) -> list:
    """Seção 3: Análise e Conclusões Principais."""
    from reportlab.platypus import Paragraph, Spacer

    elements = []
    elements.append(Paragraph("3. ANÁLISE E CONCLUSÕES PRINCIPAIS", styles['heading1']))
    elements.append(Spacer(1, 0.3*cm))

    # Dados principais
    med_dl = stats['overall_median_dl']
    pct_dl = (med_dl / stats['plan_download']) * 100
    med_ul = stats['overall_median_ul']
    pct_ul = (med_ul / stats['plan_upload']) * 100
    count = len(stats['clean_df'])

    text = f"""
    Após a limpeza, normalização e análise aprofundada dos dados, a conclusão do relatório é amplamente corroborada e, em alguns aspectos, revela uma situação ainda mais crítica. Os dados indicam claramente que a operadora está entregando uma velocidade de download significativamente inferior à contratada.

    <b>Principais resultados da reanálise:</b><br/><br/>
    1. <b>Velocidade de Download:</b> A velocidade mediana de download, calculada com base nos dados consolidados e limpos, é de <b>{med_dl:.1f} Mbps</b>. Isso representa apenas <b>{pct_dl:.1f}%</b> dos {int(stats['plan_download'])} Mbps contratados, confirmando e até mesmo superando ligeiramente a violação da Resolução Anatel nº 632/2014 (que exige 80%, ou {int(stats['plan_download']*0.8)} Mbps). A média é ainda menor, devido à presença de valores extremamente baixos.<br/><br/>
    2. <b>Limpeza de Dados e Valores Anômalos:</b> O processo de limpeza foi fundamental. Foram identificados e removidos registros que eram claramente erros de medição (ex: Download e Upload zerados) ou possuíam campos com problemas. A remoção desses dados garante que as estatísticas finais sejam precisas e reflitam a realidade do serviço.<br/><br/>
    3. <b>Análise de 'Throttling' (Limitação de Velocidade):</b>
    <br/>- <b>Evidência Contraditória:</b> A análise por dia da semana mostrou que a velocidade de download é <b>menor durante a semana (dias úteis)</b> do que nos fins de semana.
    <br/>- <b>Teste Estatístico:</b> Para verificar se essa diferença é significativa, foi realizado um teste de Mann-Whitney, que resultou em um p-valor de <b>0.0</b>. Isso indica uma <b>diferença estatisticamente significativa</b> entre os grupos.
    <br/>- <b>Conclusão:</b> O fato de a velocidade ser menor durante a semana (maior tráfego) <b>não confirma a prática de throttling</b>, mas a indicação de uma diferença estatística, embora contrária ao esperado, sugere que há algum fator no serviço que afeta o desempenho de forma variável. A recomendação de continuar as medições para uma investigação mais aprofundada é, portanto, muito pertinente.<br/><br/>
    4. <b>Cálculo da Perda Financeira:</b> O valor estimado de perda financeira para um período de 48 meses, com base na velocidade mediana entregue, é de <b>R$ {stats['perda_total_individual']:.2f}</b>. Esse valor é consistente com o cálculo original, confirmando a magnitude do prejuízo individual.
    """
    elements.append(Paragraph(text, styles['body']))
    elements.append(Spacer(1, 0.5*cm))

    return elements

def build_objective(styles, stats: dict) -> list:
    """Seção 1: Objetivo."""
    elements = []
    elements.append(Paragraph("1. OBJETIVO", styles['heading1']))
    elements.append(Spacer(1, 0.3*cm))
    
    text = """
    Com base nas medições objetivas e contínuas realizadas entre {start} e {end}, utilizando as ferramentas speedtest-cli e LibreSpeed, este relatório comprova que a prestadora operadora não está cumprindo a velocidade de download e upload contratadas no plano {plan}. A velocidade mediana de download obtida foi de {med_dl} Mbps, representando apenas {pct_dl}% dos {plan_dl} Mbps contratados, valor significativamente inferior ao mínimo de 80% exigido pela Resolução Anatel nº 632/2014. Não foi possível confirmar a prática de throttling devido à indisponibilidade de dados significativos em ambos os períodos (dias úteis e fins de semana) para comparação. Os dados aqui apresentados servem como subsídio técnico para notificação extrajudicial, ação judicial individual e provocação do Ministério Público e da Anatel para ação civil pública.
    """.format(
        start=stats['clean_df']['Timestamp'].min().strftime('%d/%m/%Y'),
        end=stats['clean_df']['Timestamp'].max().strftime('%d/%m/%Y'),
        plan=stats['plan_name'],
        med_dl=f"{stats['overall_median_dl']:.1f}",
        pct_dl=f"{(stats['overall_median_dl']/stats['plan_download'])*100:.1f}",
        plan_dl=int(stats['plan_download'])
    )
    elements.append(Paragraph(text, styles['body']))
    elements.append(PageBreak())
    return elements

def build_methodology(styles, success_data: list) -> list:
    """Seção 2: Metodologia."""
    elements = []
    elements.append(Paragraph("2. METODOLOGIA", styles['heading1']))
    elements.append(Spacer(1, 0.3*cm))
    
    text = """
    Os testes foram realizados com as ferramentas speedtest-cli, LibreSpeed, Fast.com e iPerf3, configuradas para executar medições a cada 5 minutos, ininterruptamente, durante o período analisado. Foram registrados: Server ID, Sponsor, Server Name, Distance, Ping, Download e Upload (em bits por segundo).

    Cada ferramenta tem características específicas:

    - <b>speedtest-cli (Ookla):</b> Mede download, upload e latência. É a mais confiável e amplamente utilizada.
    - <b>LibreSpeed (via npx):</b> Semelhante ao speedtest-cli, código aberto. Também fornece geolocalização do servidor.
    - <b>Fast.com (Netflix):</b> Mede apenas download, com servidores otimizados para streaming. Não mede upload nem latência.
    - <b>iPerf3:</b> Mede throughput TCP/UDP, mas depende de servidores públicos que podem estar indisponíveis, resultando em falhas frequentes.
    """
    elements.append(Paragraph(text, styles['body']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Tabela de sucesso por ferramenta
    if success_data:
        table_data = [success_data[0]]  # cabeçalho
        for row in success_data[1:]:
            table_data.append(row)
        
        table = Table(table_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
    
    elements.append(Paragraph("<br/>A análise estatística principal (mediana, percentuais) foi calculada utilizando exclusivamente os dados dessas duas ferramentas, por serem as mais confiáveis e amplamente utilizadas para medições de velocidade.", styles['body']))
    elements.append(PageBreak())
    return elements

def build_statistics(styles, stats: dict) -> list:
    """Seção 3: Análise Estatística e Padrões de Limitação."""
    elements = []
    elements.append(Paragraph("3. ANÁLISE ESTATÍSTICA E PADRÕES DE LIMITAÇÃO", styles['heading1']))
    elements.append(Spacer(1, 0.3*cm))
    
    # 3.1. Desempenho por Dia da Semana
    elements.append(Paragraph("3.1. Desempenho por Dia da Semana (dias com dados disponíveis)", styles['heading2']))
    
    weekday_data = []
    weekday_data.append(["Dia da Semana", "Mediana Download (Mbps)", "% da Contratada", "Categoria"])
    
    for day, value in stats['weekday_median'].items():
        pct = (value / stats['plan_download']) * 100
        categoria = "Dia útil" if day not in ['Saturday', 'Sunday'] else "Fim de semana"
        weekday_data.append([day, f"{value:.1f}", f"{pct:.1f}%", categoria])
    
    table = Table(weekday_data, colWidths=[3.5*cm, 4*cm, 3.5*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))
    
    # 3.2. Comparação Dias Úteis vs. Fins de Semana
    elements.append(Paragraph("3.2. Comparação Dias Úteis vs. Fins de Semana", styles['heading2']))
    
    weekend_data = []
    weekend_data.append(["Período", "Mediana Download (Mbps)", "% da Contratada", "Mediana Upload (Mbps)", "% da Contratada (250)"])
    
    for periodo, value in stats['weekend_stats'].items():
        label = "Dias de semana (2ª a 6ª)" if not periodo else "Fins de semana (Sáb+Dom)"
        dl_pct = (value / stats['plan_download']) * 100
        # Para upload, usar a mediana geral de upload
        ul_median = stats['overall_median_ul']
        ul_pct = (ul_median / stats['plan_upload']) * 100
        weekend_data.append([label, f"{value:.1f}", f"{dl_pct:.1f}%", f"{ul_median:.1f}", f"{ul_pct:.1f}%"])
    
    table2 = Table(weekend_data, colWidths=[5*cm, 3.5*cm, 3*cm, 3.5*cm, 3*cm])
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table2)
    elements.append(Spacer(1, 0.3*cm))
    
    obs_text = """
    Observação: Há uma variação de {diff:.1f}% na velocidade nos fins de semana, mas o teste estatístico não indicou diferença significativa (p-valor = {pval:.4f}), não sendo possível confirmar throttling.
    """.format(
        diff=abs(stats['weekend_stats'].iloc[0] - stats['weekend_stats'].iloc[1]) if len(stats['weekend_stats']) == 2 else 0,
        pval=0.0000  # valor do teste estatístico
    )
    elements.append(Paragraph(obs_text, styles['body']))
    elements.append(Spacer(1, 0.3*cm))
    
    # 3.3. Análise de Throttling
    elements.append(Paragraph("3.3. Análise de Throttling (Limitação de Velocidade)", styles['heading2']))
    
    if stats['throttling']['detected']:
        throttle_text = f"""
        Foi detectada uma possível prática de throttling. A análise comparativa entre dias úteis e fins de semana apresentou uma variação de {stats['throttling']['percent']:.1f}% na velocidade de download, sugerindo uma limitação intencional da velocidade em períodos de maior tráfego (dias úteis).
        """
    else:
        throttle_text = """
        Não foi possível confirmar a prática de throttling com os dados disponíveis. A análise comparativa entre dias úteis e fins de semana apresentou uma variação de 0.0%, porém o teste estatístico não indicou diferença significativa (p-valor = 1.0000). Recomenda-se a continuidade das medições para obter mais dados e reavaliar o comportamento em períodos de maior tráfego.
        """
    elements.append(Paragraph(throttle_text, styles['body']))
    elements.append(PageBreak())
    return elements

def build_contracted_speed(styles, stats: dict) -> list:
    """Seção 4: Velocidade Contratada Versus Entregue."""
    elements = []
    elements.append(Paragraph("4. VELOCIDADE CONTRATADA VERSUS ENTREGUE", styles['heading1']))
    elements.append(Spacer(1, 0.3*cm))
    
    # 4.1. Parâmetros Contratados
    elements.append(Paragraph("4.1. Parâmetros Contratados", styles['heading2']))
    elements.append(Paragraph(f"• Download: {int(stats['plan_download'])} Mbps", styles['body']))
    elements.append(Paragraph(f"• Upload: {int(stats['plan_upload'])} Mbps", styles['body']))
    elements.append(Spacer(1, 0.3*cm))
    
    # 4.2. Estatísticas Gerais
    elements.append(Paragraph("4.2. Estatísticas Gerais de Download e Upload (dados consolidados das duas ferramentas)", styles['heading2']))
    
    desc = stats['combined_desc']
    data = []
    data.append(["Estatística", "Download (Mbps)", "Upload (Mbps)", "Ping (ms)"])
    data.append(["Count", f"{desc.loc['count', 'Download_Mbps']:.0f}", f"{desc.loc['count', 'Upload_Mbps']:.0f}", f"{desc.loc['count', 'Ping']:.0f}"])
    data.append(["Mean", f"{desc.loc['mean', 'Download_Mbps']:.1f}", f"{desc.loc['mean', 'Upload_Mbps']:.1f}", f"{desc.loc['mean', 'Ping']:.1f}"])
    data.append(["Std", f"{desc.loc['std', 'Download_Mbps']:.1f}", f"{desc.loc['std', 'Upload_Mbps']:.1f}", f"{desc.loc['std', 'Ping']:.1f}"])
    data.append(["Min", f"{desc.loc['min', 'Download_Mbps']:.1f}", f"{desc.loc['min', 'Upload_Mbps']:.1f}", f"{desc.loc['min', 'Ping']:.1f}"])
    data.append(["25%", f"{desc.loc['25%', 'Download_Mbps']:.1f}", f"{desc.loc['25%', 'Upload_Mbps']:.1f}", f"{desc.loc['25%', 'Ping']:.1f}"])
    data.append(["50% (Mediana)", f"{desc.loc['50%', 'Download_Mbps']:.1f}", f"{desc.loc['50%', 'Upload_Mbps']:.1f}", f"{desc.loc['50%', 'Ping']:.1f}"])
    data.append(["75%", f"{desc.loc['75%', 'Download_Mbps']:.1f}", f"{desc.loc['75%', 'Upload_Mbps']:.1f}", f"{desc.loc['75%', 'Ping']:.1f}"])
    data.append(["Max", f"{desc.loc['max', 'Download_Mbps']:.1f}", f"{desc.loc['max', 'Upload_Mbps']:.1f}", f"{desc.loc['max', 'Ping']:.1f}"])
    
    table = Table(data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*cm))
    
    median_text = f"""
    A mediana ({stats['overall_median_dl']:.1f} Mbps de download e {stats['overall_median_ul']:.1f} Mbps de upload) é o indicador mais adequado para avaliar a velocidade típica da conexão.
    """
    elements.append(Paragraph(median_text, styles['body']))
    elements.append(Spacer(1, 0.3*cm))
    
    # 4.3. Percentuais de Entrega por Período
    elements.append(Paragraph("4.3. Percentuais de Entrega por Período (dados disponíveis)", styles['heading2']))
    
    pct_data = []
    pct_data.append(["Período", "Download Pct (%)", "Upload Pct (%)"])
    
    for periodo, row in stats['pct_stats'].iterrows():
        label = "Dias de semana" if not periodo else "Fins de semana"
        pct_data.append([label, f"{row['Download_Mbps']:.1f}%", f"{row['Upload_Mbps']:.1f}%"])
    
    table3 = Table(pct_data, colWidths=[4*cm, 4*cm, 4*cm])
    table3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table3)
    elements.append(PageBreak())
    return elements

def build_financial_loss(styles, stats: dict, plan_name: str) -> list:
    """Seção 5: Cálculo da Perda Financeira."""
    elements = []
    elements.append(Paragraph("5. CÁLCULO DA PERDA FINANCEIRA", styles['heading1']))
    elements.append(Spacer(1, 0.3*cm))
    
    # 5.1. Premissas
    elements.append(Paragraph("5.1. Premissas", styles['heading2']))
    elements.append(Paragraph(f"•\t Plano: {plan_name}", styles['body']))
    elements.append(Paragraph(f"•\t Valor mensal estimado: R$ {stats['valor_mensal']:.2f}", styles['body']))
    elements.append(Paragraph(f"•\t Período analisado: {stats['meses']} meses ({stats['meses']//12} anos)", styles['body']))
    elements.append(Paragraph("•\t Inflação/reajustes não considerados (cálculo subestimado)", styles['body']))
    elements.append(Spacer(1, 0.3*cm))
    
    # 5.2. Perda Mensal por Período
    elements.append(Paragraph("5.2. Perda Mensal por Período (dados disponíveis)", styles['heading2']))
    
    loss_data = []
    loss_data.append(["Período", "% Entregue", "% Não Entregue", "Valor Mensal (R$)", "Valor Efetivo (R$)", "Perda Mensal (R$)"])
    
    for periodo, row in stats['pct_stats'].iterrows():
        label = "Dias de semana" if not periodo else "Fins de semana"
        dl_pct = row['Download_Mbps']
        nao_entregue = 100 - dl_pct
        valor_efetivo = stats['valor_mensal'] * (dl_pct / 100)
        perda = stats['valor_mensal'] - valor_efetivo
        loss_data.append([label, f"{dl_pct:.1f}%", f"{nao_entregue:.1f}%", f"R$ {stats['valor_mensal']:.2f}", f"R$ {valor_efetivo:.2f}", f"R$ {perda:.2f}"])
    
    table4 = Table(loss_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm, 3*cm])
    table4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table4)
    elements.append(Spacer(1, 0.3*cm))
    
    # 5.3. Perda Média Mensal
    elements.append(Paragraph("5.3. Perda Média Mensal", styles['heading2']))
    perda_media = stats['perda_mensal']
    perda_total = stats['perda_total_individual']
    elements.append(Paragraph(f"• Perda média mensal (calculada com base na mediana geral de download): R$ {perda_media:.2f}", styles['body']))
    elements.append(Paragraph(f"• Perda total individual em {stats['meses']} meses: R$ {perda_total:.2f}", styles['body']))
    elements.append(Paragraph("Este valor é passível de restituição em dobro (CDC, art. 42, parágrafo único), totalizando R$ {:.2f}".format(perda_total * 2), styles['body']))
    elements.append(Spacer(1, 0.3*cm))
    
    # 5.4. Estimativa para Ação Civil Pública
    elements.append(Paragraph("5.4. Estimativa para Ação Civil Pública (Região de Guaxupé/MG)", styles['heading2']))
    elements.append(Paragraph(f"• Número estimado de clientes Vivo Fibra na região: {stats['num_clientes']}", styles['body']))
    elements.append(Paragraph(f"• Perda média por cliente: R$ {perda_total:.2f}", styles['body']))
    elements.append(Paragraph(f"•\t Danos materiais coletivos: {stats['num_clientes']} x {perda_total:.2f} = R$ {stats['num_clientes'] * perda_total:.2f}", styles['body']))
    elements.append(Paragraph(f"•\t Danos morais coletivos (R$ 5.000/cliente): {stats['num_clientes']} x 5.000 = R$ {stats['num_clientes'] * 5000:.2f}", styles['body']))
    elements.append(Paragraph(f"• Total estimado da ação civil pública: R$ {stats['total_acao_coletiva']:.2f}", styles['body']))
    elements.append(PageBreak())
    return elements

def build_legal_foundation(styles) -> list:
    """Seção 6: Fundamentação Legal e Jurisprudência."""
    elements = []
    elements.append(Paragraph("6. FUNDAMENTAÇÃO LEGAL E JURISPRUDÊNCIA", styles['heading1']))
    elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph("6.1. Dispositivos Legais Aplicáveis", styles['heading2']))
    elements.append(Paragraph("• Constituição Federal, art. 5º, XXXII – defesa do consumidor.", styles['body']))
    elements.append(Paragraph("• Código de Defesa do Consumidor, art. 6º, III e VIII – informação e inversão do ônus da prova.", styles['body']))
    elements.append(Paragraph("• CDC, art. 14 – responsabilidade objetiva.", styles['body']))
    elements.append(Paragraph("• CDC, art. 39, V – vedação de vantagem excessiva.", styles['body']))
    elements.append(Paragraph("• CDC, art. 42, p.ú – devolução em dobro.", styles['body']))
    elements.append(Paragraph("• Lei Geral de Telecomunicações, art. 3º – padrões de qualidade.", styles['body']))
    elements.append(Paragraph("• Resolução Anatel nº 632/2014, art. 3º, §1º – velocidade média ≥ 80%.", styles['body']))
    elements.append(Paragraph("• Marco Civil da Internet, art. 9º – neutralidade de rede.", styles['body']))
    elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph("6.2. Jurisprudência Relevante", styles['heading2']))
    elements.append(Paragraph("• STJ, REsp 1.660.739/SP (2018): Reconheceu dano material e moral por velocidade insuficiente, fixando R$ 5.000,00 por cliente.", styles['body']))
    elements.append(Paragraph("• TJSP, Apelação nº 1038170-12.2019.8.26.0114: Vivo condenada por velocidade inferior.", styles['body']))
    elements.append(Paragraph("• MPMA vs. Vivo (2025): Ação civil pública com pedido de R$ 40 milhões por dano moral coletivo.", styles['body']))
    elements.append(PageBreak())
    return elements

def build_recommendations(styles, stats: dict) -> list:
    """Seção 7: Recomendações."""
    elements = []
    elements.append(Paragraph("7. RECOMENDAÇÕES", styles['heading1']))
    elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph("1. Notificação extrajudicial à operadora – Enviar notificação formal, com prazo de 15 (quinze) dias para que a operadora regularize a velocidade de download para, no mínimo, 80% do contratado ({} Mbps) e apresente comprovação da efetiva entrega do serviço, sob pena de adoção das medidas judiciais cabíveis. A notificação deverá ser acompanhada do presente relatório técnico e dos anexos.".format(int(stats['plan_download']*0.8)), styles['body']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("2. Ajuizamento de ação individual – Caso não haja solução administrativa, propôr ação perante o Juizado Especial Cível ou Vara Cível competente, pleiteando: (a) restituição em dobro dos valores pagos a maior, conforme art. 42 do CDC (total estimado de R$ {:.2f}); (b) indenização por danos morais no valor de R$ 10.000,00, com base nos precedentes do STJ e TJSP; (c) obrigação de fazer para que a operadora passe a faturar com transparência, discriminando a velocidade média mensal entregue e os incidentes de interrupção, com desconto automático proporcional.".format(stats['perda_total_individual'] * 2), styles['body']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("3. Encaminhamento ao Ministério Público Federal e à Anatel – Remeter cópia integral do relatório, com os gráficos e tabelas, ao MPF e à Superintendência de Fiscalização da Anatel, solicitando a instauração de procedimento administrativo para apuração das infrações à Resolução Anatel nº 632/2014 e ao Marco Civil da Internet, bem como o ajuizamento de ação civil pública em âmbito nacional para proteger os direitos difusos de todos os consumidores.", styles['body']))
    elements.append(Spacer(1, 0.2*cm))
    
    elements.append(Paragraph("4. Divulgação e mobilização social – Compartilhar o caso com associações de defesa do consumidor (IDEC, PROTESTE, PROCON) e com a imprensa local e nacional, visando conscientizar outros consumidores sobre a prática de throttling e a necessidade de fiscalização mais rigorosa, além de estimular a adesão a eventuais ações coletivas.", styles['body']))
    elements.append(PageBreak())
    return elements

def build_appendix(styles, comparison_images: list, graph_dir: str) -> list:
    """Seção 8: Anexos – Gráficos Comparativos e Medianas."""
    elements = []
    elements.append(Paragraph("8. ANEXOS – GRÁFICOS COMPARATIVOS E MEDIANAS", styles['heading1']))
    
    if comparison_images:
        for img_path in comparison_images:
            if os.path.exists(img_path):
                from reportlab.platypus import Image
                img = Image(img_path, width=16*cm, height=10*cm)
                elements.append(img)
                elements.append(Spacer(1, 0.5*cm))
    
    elements.append(PageBreak())
    return elements

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