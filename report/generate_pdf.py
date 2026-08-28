# report/generate_pdf.py
"""Função principal de geração de relatório."""

import pandas as pd
import tempfile
from .stats import clean_data, compute_statistics, compute_success_rates
from .plots import generate_comparison_plots
from .pdf_builder import build_pdf
from .formatters import data_extenso


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza os dados para bps (converte Mbps para bps se necessário).
    
    Args:
        df: DataFrame bruto.
        
    Returns:
        DataFrame normalizado.
    """
    df = df.copy()
    
    def to_bps(value, tool):
        if pd.isna(value) or value <= 0:
            return 0
        # Se a ferramenta é librespeed e o valor é < 100000, provavelmente está em Mbps
        if tool == 'librespeed' and value < 100000:
            return value * 1e6
        # Se qualquer ferramenta tem valor < 1000, assume Mbps
        elif value < 1000:
            return value * 1e6
        return value
    
    if 'Download' in df.columns:
        df['Download'] = df.apply(lambda row: to_bps(row['Download'], row.get('Tool', '')), axis=1)
    if 'Upload' in df.columns:
        df['Upload'] = df.apply(lambda row: to_bps(row['Upload'], row.get('Tool', '')), axis=1)
    
    return df


def generate_report_from_dataframe(
    df_orig, client_name, isp_name, plan_name,
    attorney_name="", address="", bill_path=None,
    output_path="report.pdf", valor_mensal=172.00, meses=48,
    plan_download=500, plan_upload=250, num_clientes=4500
):
    """Gera um relatório PDF a partir de um DataFrame de dados de teste."""
    address = address.replace("Brazil", "Brasil")

    # Normalizar unidades
    df = normalize_data(df_orig)
    
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    else:
        df['Timestamp'] = pd.to_datetime('now')

    df['Download_Mbps'] = df['Download'] / 1e6
    df['Upload_Mbps'] = df['Upload'] / 1e6
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])

    clean = clean_data(df)
    if clean.empty:
        raise ValueError("No data from speedtest-cli or librespeed found.")

    success_data = compute_success_rates(df)

    stats = compute_statistics(clean, plan_download, plan_upload)
    stats['clean_df'] = clean

    overall_median_dl = stats['overall_median_dl']
    pct_global = (overall_median_dl / plan_download) * 100 if overall_median_dl > 0 else 0
    perda_mensal = valor_mensal * (1 - pct_global/100)
    perda_total_individual = perda_mensal * meses
    danos_materiais_coletivos = perda_total_individual * num_clientes
    danos_morais_coletivos = 5000 * num_clientes
    total_acao_coletiva = danos_materiais_coletivos + danos_morais_coletivos

    stats['perda_mensal'] = perda_mensal
    stats['perda_total_individual'] = perda_total_individual
    stats['total_acao_coletiva'] = total_acao_coletiva
    stats['pct_global'] = pct_global
    stats['valor_mensal'] = valor_mensal
    stats['meses'] = meses
    stats['plan_name'] = plan_name
    stats['plan_download'] = plan_download
    stats['plan_upload'] = plan_upload
    stats['num_clientes'] = num_clientes

    graph_dir = tempfile.mkdtemp()
    df_speed = clean[clean['Tool'] == 'speedtest-cli']
    df_librespeed = clean[clean['Tool'] == 'librespeed']
    comparison_images = generate_comparison_plots(df_speed, df_librespeed, graph_dir)

    output_path = build_pdf(
        output_path, stats, client_name, plan_name, isp_name,
        attorney_name, address, bill_path, success_data,
        comparison_images, graph_dir
    )

    print(f"PDF gerado com sucesso: {output_path}")
    return output_path