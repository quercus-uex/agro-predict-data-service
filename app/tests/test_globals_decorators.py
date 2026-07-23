import json
import os
import tempfile
from enum import Enum as PyEnum
from dataclasses import dataclass
from datetime import datetime, date
from types import SimpleNamespace
from app.extensions import db

import pytest
from sqlalchemy import select

from app.decorator.log_decorator import log
from app.globals.dto2dict import dataclass_to_json
from app.globals.convertidor_tipo import convertir_tipo
from app.globals.normalizar_json import normalizar_json
from app.globals.row2dict_converter import row2dict_converter


@dataclass
class SampleDTO:
    texto: str
    fecha: datetime


def test_normalizar_json_supports_dict_bytes_str_and_none():
    assert normalizar_json(None) is None
    assert normalizar_json({"a": 1}) == {"a": 1}
    assert normalizar_json(b'{"a": 1}') == {"a": 1}
    assert normalizar_json('{"b": 2}') == {"b": 2}

    with pytest.raises(TypeError, match="Tipo de payload no soportado"):
        normalizar_json(123)


def test_dataclass_to_json_returns_json_response():
    dto = SampleDTO(texto="hola", fecha=datetime(2026, 1, 1, 12, 0, 0))
    response = dataclass_to_json(dto)

    assert response.status_code == 200
    data = json.loads(response.get_data(as_text=True))
    assert data["texto"] == "hola"
    assert data["fecha"] == "2026-01-01T12:00:00"


def test_convertidor_tipo_converts_primitives_and_dates_and_enums():
    assert convertir_tipo("123", int) == 123
    assert convertir_tipo("false", str) == "false"
    assert convertir_tipo("2026-01-02", date) == date(2026, 1, 2)

    class ExampleEnum(PyEnum):
        VALOR = "valor"

    assert convertir_tipo("valor", ExampleEnum) == ExampleEnum.VALOR

    with pytest.raises(ValueError, match="Valor 'no' no válido"):
        convertir_tipo("no", ExampleEnum)


def test_row2dict_converter_handles_single_row_and_iterable(app):
    row = db.session.execute(select(1)).first()
    converted = row2dict_converter(row)
    assert converted == {"1": 1} or converted == {"1": 1}

    rows = [SimpleNamespace(_mapping={"a": 1}), SimpleNamespace(_mapping={"a": 2})]
    assert row2dict_converter(rows) == [{"a": 1}, {"a": 2}]


def test_log_decorator_writes_json_file(app):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as handle:
        path = handle.name

    @log(path)
    def wrapped():
        return {"status": "ok"}, 200

    with app.test_request_context("/test", method="GET", headers={"User-Agent": "pytest"}):
        result = wrapped()

    assert result == ({"status": "ok"}, 200)
    assert os.path.exists(path)

    with open(path, encoding="utf-8") as opened_file:
        line = opened_file.readline().strip()

    parsed = json.loads(line)
    assert parsed["endpoint"] == "wrapped"
    assert parsed["method"] == "GET"
    os.remove(path)
