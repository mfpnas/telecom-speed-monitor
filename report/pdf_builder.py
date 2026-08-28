# report/pdf_builder.py
"""Orquestração da construção do documento PDF."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from .sections import (
    build_cover_page, build_table_of_contents, build_objective,
    build_methodology, build_statistics, build_contracted_speed,
    build_financial_loss, build_legal_foundation, build_recommendations,
    build_appendix, build_executive_summary,
    build_smart_analysis
)
import pandas as pd


def build_styles():
    """Cria e retorna os estilos de parágrafo usados no relatório."""
    styles = getSampleStyleSheet()
    custom_styles = {
        'title': ParagraphStyle('Title', parent=styles['Title'], fontSize=20,
                                alignment=TA_CENTER, spaceAfter=12, fontName='Helvetica-Bold'),
        'subtitle': ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14,
                                   alignment=TA_CENTER, spaceAfter=10, fontName='Helvetica'),
        'heading1': ParagraphStyle('Heading1', parent=styles['Heading1'], fontSize=16,
                                   spaceAfter=8, fontName='Helvetica-Bold'),
        'heading2': ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=13,
                                   spaceAfter=6, fontName='Helvetica-Bold'),
        'body': ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                               alignment=TA_JUSTIFY, spaceAfter=6, fontName='Helvetica'),
        'centered': ParagraphStyle('Centered', parent=styles['Normal'],
                                   alignment=TA_CENTER, fontSize=10, fontName='Helvetica'),
        'left': ParagraphStyle('Left', parent=styles['Normal'],
                               alignment=TA_LEFT, fontSize=10, fontName='Helvetica'),
    }
    return custom_styles


def build_pdf(output_path: str, stats: dict, client_name: str, plan_name: str,
              isp_name: str, attorney_name: str, address: str, bill_path: str = None,
              success_data: list = None, comparison_images: list = None, graph_dir: str = None):
    """Constrói o documento PDF completo."""
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2.5*cm, bottomMargin=2*cm)

    styles = build_styles()
    story = []

    # Capa
    start_date = stats['clean_df']['Timestamp'].min().strftime('%d/%m/%Y')
    end_date = stats['clean_df']['Timestamp'].max().strftime('%d/%m/%Y')
    story.extend(build_cover_page(
        styles, client_name, plan_name, isp_name,
        start_date, end_date, len(stats['clean_df']), attorney_name
    ))

    # Sumário
    story.extend(build_table_of_contents(styles))

    # Objetivo
    story.extend(build_objective(styles, stats))

    # Metodologia
    story.extend(build_methodology(styles, success_data))

    # Estatística
    story.extend(build_statistics(styles, stats))

    # Velocidade contratada
    story.extend(build_contracted_speed(styles, stats))

    # Perda financeira
    story.extend(build_financial_loss(styles, stats, plan_name))

    # Fundamentação legal
    story.extend(build_legal_foundation(styles))

    # Recomendações
    story.extend(build_recommendations(styles, stats))

    # Anexos
    story.extend(build_appendix(styles, comparison_images, graph_dir))

    # Análise inteligente (NOVA SEÇÃO)
    story.extend(build_smart_analysis(styles, stats))

    # Resumo executivo (já contém as assinaturas)
    story.extend(build_executive_summary(styles, stats, address))

    # Fatura anexada (opcional)
    if bill_path and os.path.exists(bill_path):
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Fatura anexada (PDF)", styles['centered']))

    doc.build(story)
    return output_path