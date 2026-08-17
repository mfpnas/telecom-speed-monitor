# dashboard/report_generator.py
"""Interface para geração de relatório a partir do dashboard."""

import subprocess
import tempfile
import os
import base64
import pandas as pd
from datetime import datetime
import streamlit as st


def generate_report(
    df: pd.DataFrame,
    client_name: str,
    isp_name: str,
    plan_name: str,
    attorney_name: str,
    address: str,
    export_days: int,
    export_tool: str,
    uploaded_file,
    log_dir: str = "/app/data/logs",
    plan_download: float = 500,
    plan_upload: float = 250,
    valor_mensal: float = 172.00,
    meses: int = 48,
    num_clientes: int = 4500
) -> str:
    """
    Gera o relatório PDF via subprocess e retorna o link de download.

    Args:
        ... (outros parâmetros existentes)
        plan_download, plan_upload, valor_mensal, meses, num_clientes: novos parâmetros.

    Returns:
        String HTML com o link de download do PDF, ou string vazia em caso de erro.
    """
    threshold = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=export_days)

    if export_tool == "All Tools":
        export_df = df[df['Timestamp'] >= threshold].copy()
    else:
        export_df = df[(df['Tool'] == export_tool) & (df['Timestamp'] >= threshold)].copy()

    if export_df.empty:
        st.error("No data for the selected period and tool.")
        return ""

    # Garantir colunas necessárias
    required_cols = ['Server ID', 'Sponsor', 'Server Name', 'Distance',
                     'Ping', 'Download', 'Upload', 'Share', 'IP Address']
    for col in required_cols:
        if col not in export_df.columns:
            export_df[col] = ''

    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_csv:
        export_df.to_csv(tmp_csv.name, index=False)
        csv_path = tmp_csv.name

    bill_path = None
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            tmp_pdf.write(uploaded_file.read())
            bill_path = tmp_pdf.name

    start_str = export_df['Timestamp'].min().strftime('%Y%m%d')
    end_str = export_df['Timestamp'].max().strftime('%Y%m%d')
    safe_client = client_name.replace(' ', '_')
    safe_isp = isp_name.replace(' ', '_')
    filename = f"{datetime.now().strftime('%Y%m%d')}_{safe_isp}_{safe_client}_{start_str}-{end_str}.pdf"
    output_path = os.path.join(log_dir, filename)

    # --- CORREÇÃO DO CAMINHO ---
    # Usa o script localizado na raiz do projeto (/app/generate_pdf_report.py)
    cmd = [
        'python', '-u', '/app/generate_pdf_report.py',   # <-- caminho corrigido
        '--csv', csv_path,
        '--client', client_name,
        '--isp', isp_name,
        '--plan', plan_name,
        '--attorney', attorney_name,
        '--address', address,
        '--output', output_path,
        '--plan_download', str(plan_download),
        '--plan_upload', str(plan_upload),
        '--valor_mensal', str(valor_mensal),
        '--meses', str(meses),
        '--num_clientes', str(num_clientes)
    ]
    if bill_path:
        cmd.extend(['--bill', bill_path])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            with open(output_path, 'rb') as f:
                pdf_bytes = f.read()
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF Report</a>'
            return href
        else:
            st.error(f"PDF generation failed: {result.stderr}")
            return ""
    except Exception as e:
        st.error(f"Error: {e}")
        return ""
    finally:
        os.unlink(csv_path)
        if bill_path:
            os.unlink(bill_path)