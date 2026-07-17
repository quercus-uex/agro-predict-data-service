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
    """Cuando obtener_dias_existentes cubre todo el rango pedido, no faltan
    días y get_historico lee directamente de BD sin tocar IngestaDAO."""
    fec_init = datetime(2026, 1, 1)
    fec_fin = datetime(2026, 1, 2)

    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 21)
    monkeypatch.setattr(
        historico_service_module.HistoricDAO,
        "obtener_dias_existentes",
        lambda *args, **kwargs: {fec_init.date(), fec_fin.date()},
    )

    expected = EstacionHistDTO(type=TipoHistorico.HORA, datos=["ok"])
    monkeypatch.setattr(historico_service_module.HistoricService, "_leer_datos_ready", lambda *args, **kwargs: expected)

    result = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.HORA,
        fec_init=fec_init,
        fec_fin=fec_fin,
        codigo_estacion="EST01",
    )

    assert result is expected


def test_get_historico_retries_gap_when_previous_estado_is_failed(monkeypatch):
    """Un hueco cuyo último intento quedó en FAILED no se salta (solo se
    saltan PENDING/LOADING): se vuelve a lanzar la ingesta para ese hueco."""
    fec_init = datetime(2026, 1, 1)
    fec_fin = datetime(2026, 1, 2)

    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 21)
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_dias_existentes", lambda *args, **kwargs: set())
    monkeypatch.setattr(
        historico_service_module.IngestaDAO,
        "obtener_estado",
        lambda **kwargs: {"status": "FAILED", "error_message": "boom"},
    )

    captured = {}

    def fake_crear_ingesta(app, tipo, fec_init_gap, fec_fin_arg, codigo_estacion, provincia_id, fec_fin_hilo):
        captured["fec_init_gap"] = fec_init_gap
        captured["fec_fin_hilo"] = fec_fin_hilo

    monkeypatch.setattr(historico_service_module.HistoricService, "_crear_ingesta_y_lanzar_hilo", fake_crear_ingesta)

    result = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.SEMANA,
        fec_init=fec_init,
        fec_fin=fec_fin,
        codigo_estacion="EST01",
    )

    assert captured["fec_init_gap"] == fec_init
    assert captured["fec_fin_hilo"] == fec_fin
    assert isinstance(result, ProcesoIngestaDTO)
    assert result.status == "PENDING"


def test_get_historico_without_estado_and_without_data_launches_full_ingesta(monkeypatch):
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 7)
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_dias_existentes", lambda *args, **kwargs: set())
    monkeypatch.setattr(historico_service_module.IngestaDAO, "obtener_estado", lambda **kwargs: None)

    captured = {}

    def fake_crear_ingesta(*args, **kwargs):
        captured["fec_fin_hilo"] = kwargs["fec_fin_hilo"]

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

    assert captured["fec_fin_hilo"] == fec_fin
    assert isinstance(result, ProcesoIngestaDTO)
    assert result.status == "PENDING"


def test_get_historico_without_estado_with_partial_data_launches_partial_ingesta(monkeypatch):
    """Solo faltan los días 1-3 (4-8 ya existen): se agrupan en un único
    hueco contiguo y se lanza la ingesta solo para ese hueco."""
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 5)
    monkeypatch.setattr(historico_service_module.IngestaDAO, "obtener_estado", lambda **kwargs: None)
    monkeypatch.setattr(
        historico_service_module.HistoricDAO,
        "obtener_dias_existentes",
        lambda *args, **kwargs: {datetime(2026, 1, d).date() for d in range(4, 9)},
    )

    captured = {}

    def fake_crear_ingesta(*args, **kwargs):
        captured["fec_fin_hilo"] = kwargs["fec_fin_hilo"]

    monkeypatch.setattr(historico_service_module.HistoricService, "_crear_ingesta_y_lanzar_hilo", fake_crear_ingesta)

    result = HistoricService.get_historico(
        app=None,
        tipo=TipoHistorico.HORA,
        fec_init=datetime(2026, 1, 1),
        fec_fin=datetime(2026, 1, 8),
        codigo_estacion="EST99",
    )

    assert captured["fec_fin_hilo"] == datetime(2026, 1, 3)
    assert isinstance(result, ProcesoIngestaDTO)
    assert result.status == "PENDING"


def test_get_historico_with_full_coverage_reads_directly_without_creating_ingesta(monkeypatch):
    """Cuando ya existen todos los días del rango, no se crea ningún registro
    de ingesta: se lee directamente de BD para los tres tipos."""
    monkeypatch.setattr(historico_service_module.HistoricDAO, "obtener_id_estacion_por_str", lambda _: 5)

    fec_init = datetime(2026, 1, 3)
    fec_fin = datetime(2026, 1, 8)
    monkeypatch.setattr(
        historico_service_module.HistoricDAO,
        "obtener_dias_existentes",
        lambda *args, **kwargs: {datetime(2026, 1, d).date() for d in range(3, 9)},
    )

    calls = {"count": 0}

    def fake_create(**kwargs):
        calls["count"] += 1

    monkeypatch.setattr(historico_service_module.IngestaDAO, "create", fake_create)
    monkeypatch.setattr(
        historico_service_module.HistoricService,
        "_leer_datos_ready",
        lambda tipo, *args, **kwargs: SimpleNamespace(tipo=tipo),
    )

    result_dia = HistoricService.get_historico(
        app=None, tipo=TipoHistorico.DIA, fec_init=fec_init, fec_fin=fec_fin, codigo_estacion="EST99",
    )
    result_hora = HistoricService.get_historico(
        app=None, tipo=TipoHistorico.HORA, fec_init=fec_init, fec_fin=fec_fin, codigo_estacion="EST99",
    )
    result_semana = HistoricService.get_historico(
        app=None, tipo=TipoHistorico.SEMANA, fec_init=fec_init, fec_fin=fec_fin, codigo_estacion="EST99",
    )

    assert result_dia.tipo == TipoHistorico.DIA
    assert result_hora.tipo == TipoHistorico.HORA
    assert result_semana.tipo == TipoHistorico.SEMANA
    assert calls["count"] == 0


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
