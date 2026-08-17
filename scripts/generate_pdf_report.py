#!/usr/bin/env python3
"""Wrapper para compatibilidade com a linha de comando."""

import argparse
import sys
import pandas as pd
from report.generate_pdf import generate_report_from_dataframe


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
    # Novos parâmetros para velocidades e configurações
    parser.add_argument('--plan_download', type=float, default=500)
    parser.add_argument('--plan_upload', type=float, default=250)
    parser.add_argument('--valor_mensal', type=float, default=172.00)
    parser.add_argument('--meses', type=int, default=48)
    parser.add_argument('--num_clientes', type=int, default=4500)
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
            output_path=args.output,
            valor_mensal=args.valor_mensal,
            meses=args.meses,
            plan_download=args.plan_download,
            plan_upload=args.plan_upload,
            num_clientes=args.num_clientes
        )
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)