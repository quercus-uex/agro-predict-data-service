from datetime import datetime, date
from decimal import Decimal
import json
from flask import Response
from dataclasses import asdict, is_dataclass

def json_safe(value):
    """Convierte cualquier objeto (dataclass, Row, tuple, datetime, decimal…) a JSON-safe."""
    
    # None, int, float, bool, str → OK tal cual
    if value is None or isinstance(value, (int, float, bool, str)):
        return value
    
    # datetime / date → ISO
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    
    # Decimal → float
    if isinstance(value, Decimal):
        return float(value)
    
    # Row de SQLAlchemy
    if hasattr(value, "_mapping"):
        return {k: json_safe(v) for k, v in value._mapping.items()}
    
    # Dataclass
    if is_dataclass(value):
        return {k: json_safe(v) for k, v in asdict(value).items()}

    # Diccionario
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    
    # Lista o tupla
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    
    # Fallback: string
    return str(value)

def dataclass_to_json(obj):
    """
    Convierte cualquier dataclass (incluso anidada) a JSON serializable.
    Maneja datetime y Decimal.
    """
    response = Response(
        response=json.dumps(json_safe(obj), indent=4),
        status=200,
        mimetype='application/json'
    )
    return response