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
            output_path=args.output
        )
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)