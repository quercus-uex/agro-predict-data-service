from datetime import datetime
from decimal import Decimal
from sqlalchemy import Row

def _convert_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (Decimal, float)):
        return float(value)
    if value is None:
        return None
    return value


def row2dict_converter(data):
    # Caso 1: una sola fila
    if isinstance(data, Row):
        return {
            key: _convert_value(value)
            for key, value in data._mapping.items()
        }

    # Caso 2: iterable de filas
    return [
        {
            key: _convert_value(value)
            for key, value in row._mapping.items()
        }
        for row in data
    ]

def row2dict_list(rows):
    return [row2dict_converter(r) for r in rows]