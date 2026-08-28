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
    Otimizado para reduzir a quantidade de dados renderizados.

    Args:
        df: DataFrame com dados.
        tools: Lista de ferramentas a incluir.
        start_date: Data inicial.
        end_date: Data final.
        period: String do tipo 'Last 6 hours', 'Last 7 days', 'Complete'.

    Returns:
        DataFrame filtrado.
    """
    # Aplica filtro de ferramentas primeiro
    mask = (df['Tool'].isin(tools))
    filtered = df[mask].copy()
    
    # Filtra por período móvel (mais eficiente)
    if period != "Complete":
        if "hours" in period:
            hours = int(period.split()[1])
            cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(hours=hours)
        elif "days" in period:
            days = int(period.split()[1])
            cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
        else:
            cutoff = None
        if cutoff is not None:
            filtered = filtered[filtered['Timestamp'] >= cutoff]
    else:
        # Se for "Complete", filtra por intervalo de datas selecionado
        filtered = filtered[
            (filtered['Timestamp'].dt.date >= start_date) &
            (filtered['Timestamp'].dt.date <= end_date)
        ]

    return filtered