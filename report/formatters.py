# report/formatters.py
"""Funções de formatação para moeda, números e datas brasileiras."""

import pandas as pd
from datetime import datetime
from typing import Union


def format_br_money(value: Union[float, int, None]) -> str:
    """Formata um valor numérico para moeda brasileira (R$).

    Args:
        value: Valor a ser formatado.

    Returns:
        String no formato 'R$ 1.234,56'.
    """
    if pd.isna(value) or value is None:
        return "R$ 0,00"
    formatted = f"{value:,.2f}"
    parts = formatted.split('.')
    integer_part = parts[0].replace(',', '.')
    decimal_part = parts[1] if len(parts) > 1 else '00'
    return f"R$ {integer_part},{decimal_part}"


def format_currency(value: Union[float, int, None]) -> str:
    """Alias para format_br_money."""
    return format_br_money(value)


def format_br_number(value: Union[float, int, None]) -> str:
    """Formata um número com duas casas decimais no padrão brasileiro.

    Args:
        value: Valor a ser formatado.

    Returns:
        String no formato '1.234,56'.
    """
    if pd.isna(value) or value is None:
        return "0,00"
    formatted = f"{value:,.2f}"
    parts = formatted.split('.')
    integer_part = parts[0].replace(',', '.')
    decimal_part = parts[1] if len(parts) > 1 else '00'
    return f"{integer_part},{decimal_part}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Formata um valor como porcentagem.

    Args:
        value: Valor a ser formatado (ex: 0.1234 para 12.34%).
        decimals: Número de casas decimais.

    Returns:
        String no formato '12.3%'.
    """
    if pd.isna(value) or value is None:
        return "0.0%"
    return f"{value * 100:.{decimals}f}%"


def format_mbps(value: Union[float, int, None]) -> str:
    """Formata um valor em Mbps com uma casa decimal.

    Args:
        value: Valor em Mbps.

    Returns:
        String no formato '123.4 Mbps'.
    """
    if pd.isna(value) or value is None:
        return "0.0 Mbps"
    return f"{value:.1f} Mbps"


def data_extenso(dt: datetime) -> str:
    """Converte uma data para o formato extenso em português.

    Exemplo: '14 de Agosto de 2026'

    Args:
        dt: Objeto datetime.

    Returns:
        String com a data por extenso.
    """
    if dt is None:
        dt = datetime.now()
    
    meses = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    return f"{dt.day} de {meses[dt.strftime('%B')]} de {dt.year}"