from datetime import datetime
from types import SimpleNamespace

import pytest

from app.historicos.historico_dto import EstacionHistDTO, ProvinciaHistDTO, TipoHistorico
from app.ingesta.ingesta_dto import ProcesoIngestaDTO
from app.historicos.historico_service import HistoricService
import app.historicos.historico_service as historico_service_module


def test_horas_pico_returns_value_or_none():
    horas_pico = {
        "hora_temp_max": (datetime(2026, 1, 1, 0, 0), 1),
        "hora_temp_min": (datetime(2026, 1, 2, 0, 0), 3),
    }

    assert HistoricService._horas_pico(horas_pico, "hora_temp_min") == (datetime(2026, 1, 2, 0, 0), 3)
    assert HistoricService._horas_pico(horas_pico, "unknown_key") is None


def test_estaciones_usadas_for_provincia_and_estacion_scope():
    payload = {"estaciones_usadas": ["EST01", "EST02"]}

    assert HistoricService._estaciones_usadas(payload, estacion_id=None) == ["EST01", "EST02"]
    assert HistoricService._estaciones_usadas(payload, estacion_id=12) is None


def test_comprobar_devolucion_returns_provincia_dto():
    data = ["item"]

    result = HistoricService.comprobar_devolucion(
        estacion_id=None,
        provincia_id=99,
        tipo=TipoHistorico.DIA,
        datos=data,
    )

    assert isinstance(result, ProvinciaHistDTO)
    assert result.type == TipoHistorico.DIA
    assert result.datos == data


def test_comprobar_devolucion_returns_estacion_dto():
    data = ["item"]

    result = HistoricService.comprobar_devolucion(
        estacion_id=10,
        provincia_id=None,
        tipo=TipoHistorico.HORA,
        datos=data,
    )

    assert isinstance(result, EstacionHistDTO)
    assert result.type == TipoHistorico.HORA
    assert result.datos == data


def test_comprobar_devolucion_raises_if_no_scope():
    with pytest.raises(ValueError, match="Se debe proporcionar estacion_id o provincia_id"):
        HistoricService.comprobar_devolucion(
            estacion_id=None,
            provincia_id=None,
            tipo=TipoHistorico.SEMANA,
            datos=[],
        )


def test_get_historico_raises_when_no_estacion_or_provincia():
    with pytest.raises(ValueError, match="Debe indicarse la estación o provincia"):
        HistoricService.get_historico(
            app=None,
            tipo=TipoHistorico.DIA,
            fec_init=datetime(2026, 1, 1),
            fec_fin=datetime(2026, 1, 2),
        )


def test_get_historico_returns_pending_when_estado_pending(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 11)
    monkeypatch.setattr(
        historico_service_module.IngestaDAO,
        "obtener_estado",
        lambda **kwargs: {"status": "PENDING"},
    )

    result = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.DIA,
        fec_init=datetime(2026, 1, 1),
        fec_fin=datetime(2026, 1, 2),
        codigo_estacion="EST01",
    )

    assert isinstance(result, ProcesoIngestaDTO)
    assert result.status == "PENDING"
    assert result.datos_solicitados == TipoHistorico.DIA.value


def test_get_historico_ready_uses_read_data_path(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 21)
    monkeypatch.setattr(
        historico_service_module.IngestaDAO,
        "obtener_estado",
        lambda **kwargs: {"status": "READY"},
    )

    expected = EstacionHistDTO(type=TipoHistorico.HORA, datos=["ok"])
    monkeypatch.setattr(historico_service_module.HistoricService, "_leer_datos_ready", lambda *args, **kwargs: expected)

    result = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.HORA,
        fec_init=datetime(2026, 1, 1),
        fec_fin=datetime(2026, 1, 2),
        codigo_estacion="EST01",
    )

    assert result is expected


def test_get_historico_returns_error_dto_for_failed_estado(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 21)
    monkeypatch.setattr(
        historico_service_module.IngestaDAO,
        "obtener_estado",
        lambda **kwargs: {
            "status": "FAILED",
            "zona": "estacion",
            "day": 1,
            "month": 1,
            "year": 2026,
            "started_at": datetime(2026, 1, 1, 9, 0),
            "error_message": "boom",
        },
    )

    result = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.SEMANA,
        fec_init=datetime(2026, 1, 1),
        fec_fin=datetime(2026, 1, 2),
        codigo_estacion="EST01",
    )

    assert isinstance(result, ProcesoIngestaDTO)
    assert result.status == "FAILED"
    assert "Semana - estacion" in result.datos_solicitados
    assert result.error == "boom"


def test_get_historico_without_estado_and_without_data_launches_full_ingesta(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 7)
    monkeypatch.setattr(historico_service_module.IngestaDAO, "obtener_estado", lambda **kwargs: None)
    monkeypatch.setattr(historico_service_module.HistoricDAO, "define_computing_general", lambda *args, **kwargs: None)

    captured = {}

    def fake_crear_ingesta(*args, **kwargs):
        captured["fec_fin_hilo"] = kwargs["fec_fin_hilo"]
        return "INGESTA_START"

    monkeypatch.setattr(historico_service_module.HistoricService, "_crear_ingesta_y_lanzar_hilo", fake_crear_ingesta)

    fec_init = datetime(2026, 1, 1)
    fec_fin = datetime(2026, 1, 5)

    result = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.DIA,
        fec_init=fec_init,
        fec_fin=fec_fin,
        codigo_estacion="EST99",
    )

    assert result == "INGESTA_START"
    assert captured["fec_fin_hilo"] == fec_fin


def test_get_historico_without_estado_with_partial_data_launches_partial_ingesta(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 5)
    monkeypatch.setattr(historico_service_module.IngestaDAO, "obtener_estado", lambda **kwargs: None)

    partial_row = SimpleNamespace(timestamp=datetime(2026, 1, 3, 10, 0))
    monkeypatch.setattr(
        historico_service_module.HistoricDAO,
        "define_computing_general",
        lambda *args, **kwargs: partial_row,
    )

    captured = {}

    def fake_crear_ingesta(*args, **kwargs):
        captured["fec_fin_hilo"] = kwargs["fec_fin_hilo"]
        return "PARTIAL"

    monkeypatch.setattr(historico_service_module.HistoricService, "_crear_ingesta_y_lanzar_hilo", fake_crear_ingesta)

    result = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.HORA,
        fec_init=datetime(2026, 1, 1),
        fec_fin=datetime(2026, 1, 8),
        codigo_estacion="EST99",
    )

    assert result == "PARTIAL"
    assert captured["fec_fin_hilo"] == datetime(2026, 1, 3).date()


def test_get_historico_without_estado_with_full_coverage_creates_ready(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 5)
    monkeypatch.setattr(historico_service_module.IngestaDAO, "obtener_estado", lambda **kwargs: None)

    fec_init = datetime(2026, 1, 3)
    full_row = SimpleNamespace(timestamp=fec_init)
    monkeypatch.setattr(
        historico_service_module.HistoricDAO,
        "define_computing_general",
        lambda *args, **kwargs: full_row,
    )

    calls = {"count": 0}

    def fake_create(**kwargs):
        calls["count"] += 1

    monkeypatch.setattr(historico_service_module.IngestaDAO, "create", fake_create)

    result_dia = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.DIA,
        fec_init=fec_init,
        fec_fin=datetime(2026, 1, 8),
        codigo_estacion="EST99",
    )

    monkeypatch.setattr(historico_service_module.IngestaDAO, "create", fake_create)

    result_hora = HistoricService.get_historico(
        app = None,
        tipo = TipoHistorico.HORA,
        fec_init = fec_init,
        fec_fin = datetime(2026, 1, 8),
        codigo_estacion = "EST99"
    )

    monkeypatch.setattr(historico_service_module.IngestaDAO, "create", fake_create)

    result_semana = HistoricService.get_historico(
        app = None,
        tipo = TipoHistorico.SEMANA,
        fec_init = fec_init,
        fec_fin = datetime(2026, 1, 8),
        codigo_estacion = "EST99"
    )

    assert isinstance(result_dia, ProcesoIngestaDTO)
    assert isinstance(result_hora, ProcesoIngestaDTO)
    assert isinstance(result_semana, ProcesoIngestaDTO)
    assert result_dia.status == "READY"
    assert result_hora.status == "READY"
    assert result_semana.status == "READY"
    assert result_dia.datos_solicitados == TipoHistorico.DIA.value
    assert result_hora.datos_solicitados == TipoHistorico.HORA.value
    assert result_semana.datos_solicitados == TipoHistorico.SEMANA.value
    assert calls["count"] == 3


def test_leer_datos_ready_uses_tipo_config_and_builder(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_provincia_por_str", lambda provincia_id: 77)

    def fake_dao_fn(estacion_id, provincia_id, fec_init, fec_fin):
        assert estacion_id == 15
        assert provincia_id == 77
        return {"payload": "dao"}

    def fake_build_fn(data, estacion_id):
        assert data == {"payload": "dao"}
        assert estacion_id == 15
        return ["built"]

    def fake_wrap_dia (estacion_id, provincia_id, tipo, datos):
        assert tipo == TipoHistorico.DIA
        return {"wrapped": datos, "provincia": provincia_id, "estacion": estacion_id}
    
    def fake_wrap_hora (estacion_id, provincia_id, tipo, datos):
        assert tipo == TipoHistorico.HORA
        return {"wrapped": datos, "provincia": provincia_id, "estacion": estacion_id}
    
    def fake_wrap_semana (estacion_id, provincia_id, tipo, datos):
        assert tipo == TipoHistorico.SEMANA
        return {"wrapped": datos, "provincia": provincia_id, "estacion": estacion_id}

    monkeypatch.setattr(historico_service_module.HistoricService, "_build_historico_dia", staticmethod(fake_build_fn))
    monkeypatch.setattr(historico_service_module.HistoricService, "comprobar_devolucion", staticmethod(fake_wrap_dia))
    monkeypatch.setitem(
        historico_service_module._TIPO_CONFIG,
        TipoHistorico.DIA,
        (fake_dao_fn, "_build_historico_dia", "valores_diarios"),
    )

    result_dia = HistoricService._leer_datos_ready(
        tipo=TipoHistorico.DIA,
        estacion_id=15,
        provincia_id="CC",
        fec_init=datetime(2026, 1, 1),
        fec_fin=datetime(2026, 1, 2),
    )

    monkeypatch.setattr(historico_service_module.HistoricService, "_build_historico_hora", staticmethod(fake_build_fn))
    monkeypatch.setattr(historico_service_module.HistoricService, "comprobar_devolucion", staticmethod(fake_wrap_hora))
    monkeypatch.setitem(
        historico_service_module._TIPO_CONFIG,
        TipoHistorico.HORA,
        (fake_dao_fn, "_build_historico_hora", "valores_horarios"),
    )

    result_hora = HistoricService._leer_datos_ready(
        tipo=TipoHistorico.HORA,
        estacion_id=15,
        provincia_id="CC",
        fec_init=datetime(2026, 1, 1),
        fec_fin=datetime(2026, 1, 2),
    )

    monkeypatch.setattr(historico_service_module.HistoricService, "_build_historico_semana", staticmethod(fake_build_fn))
    monkeypatch.setattr(historico_service_module.HistoricService, "comprobar_devolucion", staticmethod(fake_wrap_semana))
    monkeypatch.setitem(
        historico_service_module._TIPO_CONFIG,
        TipoHistorico.SEMANA,
        (fake_dao_fn, "_build_historico_semana", "valores_semanales"),
    )

    result_semana = HistoricService._leer_datos_ready(
        tipo=TipoHistorico.SEMANA,
        estacion_id=15,
        provincia_id="CC",
        fec_init=datetime(2026, 1, 1),
        fec_fin=datetime(2026, 1, 2),
    )

    assert result_hora == {"wrapped": ["built"], "provincia": 77, "estacion": 15}
    assert result_dia == {"wrapped": ["built"], "provincia": 77, "estacion": 15}
    assert result_semana == {"wrapped": ["built"], "provincia": 77, "estacion": 15}


def test_leer_datos_ready_raises_for_unsupported_tipo(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_provincia_por_str", lambda provincia_id: 1)

    monkeypatch.setitem(
        historico_service_module._TIPO_CONFIG,
        TipoHistorico.MES,
        (None, None, None),
    )

    with pytest.raises(NotImplementedError, match="Tipo TipoHistorico.MES no implementado"):
        HistoricService._leer_datos_ready(
            tipo=TipoHistorico.MES,
            estacion_id=None,
            provincia_id="CC",
            fec_init=datetime(2026, 1, 1),
            fec_fin=datetime(2026, 1, 2),
        )
