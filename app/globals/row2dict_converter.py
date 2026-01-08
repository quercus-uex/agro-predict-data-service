from datetime import datetime
from decimal import Decimal

def row2dict_converter(data):
    valores = []
    for row in data:
        row_dict = {}
        for key, value in row._mapping.items():
            if isinstance(value, datetime):
                row_dict[key] = value.isoformat()
            elif isinstance(value, (Decimal, float)):
                row_dict[key] = float(value)
            elif value is None:
                row_dict[key] = None
            else:
                try:
                    row_dict[key] = value
                except TypeError:
                    row_dict[key] = str(value)

        valores.append(row_dict)
    
    return valores

def row2dict_list(rows):
    return [row2dict_converter(r) for r in rows]