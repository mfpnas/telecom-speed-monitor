"""Função principal de geração de relatório."""

import pandas as pd
import tempfile
from .stats import clean_data, compute_statistics, compute_success_rates
from .plots import generate_comparison_plots
from .pdf_builder import build_pdf
from .formatters import data_extenso


def generate_report_from_dataframe(df_orig, client_name, isp_name, plan_name,
                                   attorney_name="", address="", bill_path=None,
                                   output_path="report.pdf", valor_mensal=172.00, meses=48):
    """Gera um relatório PDF a partir de um DataFrame de dados de teste.

    Args:
        df_orig: DataFrame bruto (com colunas 'Tool', 'Download', 'Upload', etc.).
        client_name: Nome do cliente.
        isp_name: Nome da operadora.
        plan_name: Nome do plano.
        attorney_name: Nome do advogado (opcional).
        address: Endereço.
        bill_path: Caminho para a fatura (opcional).
        output_path: Caminho de saída do PDF.
        valor_mensal: Valor mensal do plano.
        meses: Número de meses analisados.

    Returns:
        Caminho do arquivo PDF gerado.
    """
    # Corrigir grafia
    address = address.replace("Brazil", "Brasil")

    df = df_orig.copy()
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    else:
        df['Timestamp'] = pd.to_datetime('now')

    # Converter para Mbps
    df['Download_Mbps'] = df['Download'] / 1e6
    df['Upload_Mbps'] = df['Upload'] / 1e6
    df['DayOfWeek'] = df['Timestamp'].dt.day_name()
    df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])

    # Limpeza e estatísticas
    clean = clean_data(df)
    if clean.empty:
        raise ValueError("No data from speedtest-cli or librespeed found.")

    success_data = compute_success_rates(df)

    stats = compute_statistics(clean)
    stats['clean_df'] = clean  # adiciona o DataFrame para uso nas seções

    # Cálculo de perdas
    overall_median_dl = stats['overall_median_dl']
    pct_global = (overall_median_dl / 500) * 100 if overall_median_dl > 0 else 0
    perda_mensal = valor_mensal * (1 - pct_global/100)
    perda_total_individual = perda_mensal * meses
    danos_materiais_coletivos = perda_total_individual * 4500
    danos_morais_coletivos = 5000 * 4500
    total_acao_coletiva = danos_materiais_coletivos + danos_morais_coletivos

    stats['perda_mensal'] = perda_mensal
    stats['perda_total_individual'] = perda_total_individual
    stats['total_acao_coletiva'] = total_acao_coletiva
    stats['pct_global'] = pct_global
    stats['valor_mensal'] = valor_mensal
    stats['meses'] = meses
    stats['plan_name'] = plan_name

    # Gerar gráficos
    graph_dir = tempfile.mkdtemp()
    df_speed = clean[clean['Tool'] == 'speedtest-cli']
    df_librespeed = clean[clean['Tool'] == 'librespeed']
    comparison_images = generate_comparison_plots(df_speed, df_librespeed, graph_dir)

    # Construir PDF
    output_path = build_pdf(
        output_path, stats, client_name, plan_name, isp_name,
        attorney_name, address, bill_path, success_data,
        comparison_images, graph_dir
    )

    print(f"PDF gerado com sucesso: {output_path}")
    return output_path