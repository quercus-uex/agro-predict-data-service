import json
import os
import base64
import tempfile
from enum import Enum as PyEnum
from dataclasses import dataclass
from datetime import datetime, date
from types import SimpleNamespace
from app.extensions import db
from helpers.ApiExceptions import APIException
from unittest.mock import MagicMock, patch

import pytest
from flask import jsonify
from sqlalchemy import select

from app.decorator.log_decorator import log
from app.decorator.token_decorator import (
    get_jwks_keys,
    get_public_key,
    token_required,
)
from app.globals.dto2dict import dataclass_to_json
from app.globals.convertidor_tipo import convertir_tipo
from app.globals.normalizar_json import normalizar_json
from app.globals.row2dict_converter import row2dict_converter
from helpers.ApiExceptions import APIException


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


def test_token_required_decorator_allows_valid_token(app, monkeypatch):
    app.config["KEYCLOAK_CLIENT_ID"] = "test-client"

    with app.test_request_context(
        "/secure",
        method="GET",
        headers={"Authorization": "Bearer token123"},
    ):
        monkeypatch.setattr(
            "app.decorator.token_decorator.get_jwks_keys",
            lambda: {"keys": [{"kid": "kid1", "x5c": ["cert"]}]},
        )
        monkeypatch.setattr(
            "app.decorator.token_decorator.jwt.get_unverified_header",
            lambda token: {"kid": "kid1"},
        )
        monkeypatch.setattr(
            "app.decorator.token_decorator.jwt.decode",
            lambda token, key, algorithms, audience, options: {"preferred_username": "user", "roles": ["public"]},
        )

        @token_required(roles=["public"])
        def secured():
            return "ok"

        assert secured() == "ok"


def test_token_required_returns_401_when_no_authorization_header(app):
    with app.test_request_context("/secure", method="GET"):

        @token_required(roles=["public"])
        def secured():
            return "ok"

        result = None
        with pytest.raises(APIException) as exc_info:
            result = secured()

        assert exc_info.value.status == 401
        assert exc_info.value.error == "Token required"
        assert result is None


def test_get_jwks_keys_uses_cached_result(monkeypatch, app):
    with app.app_context():
        from app.decorator import token_decorator

        token_decorator._jwks_cache = None

        class FakeResponse:
            def raise_for_status(self):
                pass
            def json(self):
                return {"keys": [{"kid": "kid1"}]}

        monkeypatch.setattr("requests.get", lambda url, timeout, verify: FakeResponse())

        first = get_jwks_keys()
        second = get_jwks_keys()

        assert first == second

def make_fake_jwt(kid: str) -> str:
    def b64_encode(data: dict) -> str:
        json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
        return base64.urlsafe_b64encode(json_bytes).decode('utf-8').rstrip('=')
    
    header = b64_encode({"alg": "RS256", "typ": "JWT", "kid": kid})
    payload = b64_encode({"sub": "test"})
    signature = base64.urlsafe_b64encode(b"fakesig").decode('utf-8').rstrip('=')
    return f"{header}.{payload}.{signature}"

def test_get_public_key_matches_kid(app):
    with app.app_context():
        jwks = {"keys": [{"kid": "kid1", "x5c": ["cert"]}]}
        token = make_fake_jwt("kid1")
        key = get_public_key(token, jwks)
        assert key["kid"] == "kid1"

        with pytest.raises(Exception):
            get_public_key("dummy", {"keys": []})
