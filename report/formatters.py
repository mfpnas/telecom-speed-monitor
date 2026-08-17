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


def data_extenso(dt: datetime) -> str:
    """Converte uma data para o formato extenso em português.

    Exemplo: '14 de Agosto de 2026'

    Args:
        dt: Objeto datetime.

    Returns:
        String com a data por extenso.
    """
    meses = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    return f"{dt.day} de {meses[dt.strftime('%B')]} de {dt.year}"