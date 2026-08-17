"""Funções de filtragem para o dashboard."""

import pandas as pd
from datetime import date
from typing import List


def apply_time_filters(
    df: pd.DataFrame,
    tools: List[str],
    start_date: date,
    end_date: date,
    period: str
) -> pd.DataFrame:
    """
    Aplica filtros de ferramenta, intervalo de datas e período móvel.

    Args:
        df: DataFrame com dados.
        tools: Lista de ferramentas a incluir.
        start_date: Data inicial.
        end_date: Data final.
        period: String do tipo 'Últimas 6 horas', 'Últimos 3 dias', 'Completo'.

    Returns:
        DataFrame filtrado.
    """
    mask = (
        (df['Tool'].isin(tools)) &
        (df['Timestamp'].dt.date >= start_date) &
        (df['Timestamp'].dt.date <= end_date)
    )
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
        if cutoff is not None:
            filtered = filtered[filtered['Timestamp'] >= cutoff]

    return filtered