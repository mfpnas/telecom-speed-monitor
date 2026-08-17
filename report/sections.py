"""Construção de cada seção do relatório PDF."""

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
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
        ("9. RESUMO EXECUTIVO", 11),
    ]
    for texto, pag in itens:
        linha = f"{texto} ....................... {pag}"
        story.append(Paragraph(linha, styles['body']))
    story.append(PageBreak())
    return story


# Demais funções (build_objective, build_methodology, etc.) seguem o mesmo padrão,
# extraídas do código original, com docstrings e ajustes PEP8.
# Para economia de espaço, continuarei com o restante do código nos arquivos finais.