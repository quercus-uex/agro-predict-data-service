import json

def normalizar_json(payload):
    if payload is None:
        return None
    elif isinstance(payload, dict):
        return payload
    elif isinstance(payload, bytes):
        return json.loads(payload.decode("utf-8"))
    elif isinstance(payload, str):
        return json.loads(payload)
    else:
        raise TypeError(f"Tipo de payload no soportado : {type(payload)}")