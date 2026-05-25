from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.forecast.forecast_service import ForecastService
from app.forecast.forecast_dto import TipoPrediccion, TipoZona, ForecastDTO, TemperaturaLocalidadDTO
from app.ingesta.ingesta_dao import IngestaDAO
from app.forecast.forecast_dao import ForecastDAO


def test_build_localidades_transforms_rows():
    data = [
        {"nombre": "Sevilla", "nombre_normalizado": "sevilla", "altitud": 50, "latitud": 37.39, "longitud": -5.99, "codigo": "SE"}
    ]
    resultado = ForecastService._build_localidades(data)

    assert len(resultado) == 1
    assert resultado[0].nombre == "Sevilla"
    assert resultado[0].provincia == "SE"


def test_build_data_for_dto_creates_correct_dto_for_ccaa(monkeypatch):
    data_prediccion = {
        "tipo_prediccion": "actual", 
        "tipo_zona": "ccaa", 
        "codigo_zona": "EXT", 
        "fecha_prediccion": date(2026, 1, 1), 
        "fecha_elaboracion": datetime(2026, 1, 1, 10, 0), 
        "estado_cielo": "sol",
        "ccaa" : "EXT"}
    localidad = [{"nombre": "Localidad", "temperatura_maxima": 15, "temperatura_minima": 5}]
    temperaturas_localidades_dto = [TemperaturaLocalidadDTO(**loc) for loc in localidad]
    resultado_dto = ForecastDTO(**data_prediccion, temperatura_localidades = temperaturas_localidades_dto)
    monkeypatch.setattr(ForecastDAO, "_get_predicciones", staticmethod(lambda **kwargs: data_prediccion))
    monkeypatch.setattr(ForecastDAO, "_get_localidades_climaticas", staticmethod(lambda **kwargs: localidad))
    monkeypatch.setattr(ForecastService, "_build_forecast", staticmethod(lambda **kwargs: resultado_dto))

    resultado = ForecastService._build_data_for_dto(
        ccaa_id="EXT",
        provincia_id=None,
        tipo_zona="ccaa",
        tipo_prediccion="actual",
        fecha_prediccion=date(2026, 1, 1),
    )

    assert resultado.tipo_zona == "ccaa"
    assert resultado.provincia is None
    assert resultado.ccaa == "EXT"
    assert resultado.tendencia_temp_general is None
    assert resultado.temperatura_localidades[0].nombre == "Localidad"


def test_get_forecast_raises_when_both_ids_are_provided():
    with pytest.raises(ValueError, match="Debe indicarse como máximo uno de los dos identificadores"):
        ForecastService.get_forecast(
            app=None,
            ccaa_id="1",
            provincia_id="2",
            tipo_prediccion=TipoPrediccion.ACTUAL,
            tipo_zona=TipoZona.CCAA,
        )


def test_get_forecast_returns_proceso_ingesta_when_estado_pending(monkeypatch):
    monkeypatch.setattr(IngestaDAO, "obtener_estado", staticmethod(lambda **kwargs: {"status": "PENDING"}))

    resultado = ForecastService.get_forecast(
        app=None,
        ccaa_id="1",
        provincia_id=None,
        tipo_prediccion=TipoPrediccion.ACTUAL,
        tipo_zona=TipoZona.CCAA,
    )

    assert resultado.status == "PENDING"
    assert resultado.datos_solicitados == TipoPrediccion.ACTUAL.value


def test_get_forecast_returns_data_dto_when_estado_ready(monkeypatch):
    data_prediccion = {"tipo_prediccion": "actual", "tipo_zona": "ccaa", "codigo_zona": "CC", "fecha_prediccion": date.today(), "fecha_elaboracion": datetime.now(), "estado_cielo": "sol"}
    localidad = [{"nombre": "Localidad", "temperatura_maxima": 15, "temperatura_minima": 5}]
    temperaturas_localidades_dto = [TemperaturaLocalidadDTO(**loc) for loc in localidad]
    resultado_dto = ForecastDTO(**data_prediccion, temperatura_localidades = temperaturas_localidades_dto)
    monkeypatch.setattr(IngestaDAO, "obtener_estado", staticmethod(lambda **kwargs: {"status": "READY"}))
    monkeypatch.setattr(ForecastDAO, "_get_predicciones", staticmethod(lambda **kwargs: data_prediccion))
    monkeypatch.setattr(ForecastDAO, "_get_localidades_climaticas", staticmethod(lambda **kwargs: localidad))
    monkeypatch.setattr(ForecastService, "_build_forecast", staticmethod(lambda **kwargs: resultado_dto))
    monkeypatch.setattr(ForecastService, '_build_data_for_dto', staticmethod(lambda **kwargs: resultado_dto))

    resultado = ForecastService.get_forecast(
        app=None,
        ccaa_id="1",
        provincia_id=None,
        tipo_prediccion=TipoPrediccion.ACTUAL,
        tipo_zona=TipoZona.CCAA,
    )
    print(resultado)
    assert resultado.type_zone == TipoZona.CCAA
    assert resultado.type_prediction == TipoPrediccion.ACTUAL
    assert isinstance(resultado.datos, ForecastDTO)


def test_get_forecast_creates_pending_if_no_estado(monkeypatch):
    monkeypatch.setattr(IngestaDAO, "obtener_estado", staticmethod(lambda **kwargs: None))
    monkeypatch.setattr(IngestaDAO, "create", staticmethod(lambda **kwargs: None))
    monkeypatch.setattr("app.forecast.forecast_service.lanzar_ingesta_background", lambda *args, **kwargs: None)

    resultado = ForecastService.get_forecast(
        app=None,
        ccaa_id=None,
        provincia_id=None,
        tipo_prediccion=TipoPrediccion.ACTUAL,
        tipo_zona=TipoZona.NACIONAL,
    )

    assert resultado.status == "PENDING"
    assert resultado.datos_solicitados == TipoPrediccion.ACTUAL.value
