"""Funções de filtragem para o dashboard."""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional


def apply_time_filters(df: pd.DataFrame, tools: List[str],
                       start_date: datetime.date, end_date: datetime.date,
                       period: str) -> pd.DataFrame:
    """Aplica filtros de ferramenta, intervalo de datas e período móvel.

    Args:
        df: DataFrame com dados.
        tools: Lista de ferramentas a incluir.
        start_date: Data inicial (date object).
        end_date: Data final.
        period: String do tipo 'Últimas 6 horas', 'Últimos 3 dias', 'Completo'.

    Returns:
        DataFrame filtrado.
    """
    mask = (df['Tool'].isin(tools)) & (df['Timestamp'].dt.date >= start_date) & (df['Timestamp'].dt.date <= end_date)
    filtered = df[mask].copy()

    if period != "Completo":
        if "horas" in period:
            hours = int(period.split()[1])
            cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(hours=hours)
        elif "dias" in period:
            days = int(period.split()[1])
            cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
        else:
            cutoff = None
        if cutoff:
            filtered = filtered[filtered['Timestamp'] >= cutoff]

    return filtered