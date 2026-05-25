from datetime import datetime, timedelta
from uuid import uuid4

from app.historicos.historico_dao import HistoricDAO
from app.models import CCAA, Provincia, Estacion, MedicionClimatica
from app.extensions import db


def unique_code(prefix):
    return f"{prefix}_{uuid4().hex[:8]}"


class DummyRow:
    def __init__(self, mapping):
        self._mapping = mapping

    def __getitem__(self, item):
        return self._mapping[item]


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


def create_historico_entities():
    ccaa_codigo = unique_code("CCAA")
    provincia_codigo = unique_code("CC")
    estacion_codigo = unique_code("EST")

    ccaa = CCAA(codigo=ccaa_codigo, nombre="Comunidad de prueba")
    provincia = Provincia(codigo=provincia_codigo, nombre="Cáceres", ccaa=ccaa)
    estacion = Estacion(
        codigo=estacion_codigo,
        nombre="Estación prueba",
        longitud="-1.0",
        latitud="42.0",
        altitud=100,
        provincia=provincia,
    )

    db.session.add_all([ccaa, provincia, estacion])
    db.session.commit()
    return ccaa, provincia, estacion


def create_medicion(estacion, provincia, timestamp, temperatura, humedad):
    medicion = MedicionClimatica(
        estacion=estacion,
        provincia=provincia,
        timestamp=timestamp,
        temperatura=temperatura,
        humedad=humedad,
        vel_viento=5.0,
        precipitacion=0.0,
        etp_mon=1.0,
        pep_mon=1.0,
        radiacion=10.0,
        semana=1,
        mes=1,
        anio=2026,
    )
    db.session.add(medicion)
    db.session.commit()
    return medicion


def test_obtener_id_provincia_exito(app):
    _, provincia, _ = create_historico_entities()

    resultado = HistoricDAO.obtener_id_provincia_por_str(provincia.codigo)

    assert resultado == provincia.id


def test_obtener_id_provincia_excepcion(app, monkeypatch):
    def mock_execute(*args, **kwargs):
        raise Exception("Error simulado de conexion")

    monkeypatch.setattr(db.session, "execute", mock_execute)

    resultado = HistoricDAO.obtener_id_provincia_por_str("CC")

    assert resultado == []


def test_obtener_id_estacion_exito(app):
    _, _, estacion = create_historico_entities()

    resultado = HistoricDAO.obtener_id_estacion_por_str(estacion.codigo)

    assert resultado == estacion.id


def test_obtener_id_estacion_excepcion(app, monkeypatch):
    def mock_query(*args, **kwargs):
        raise Exception("Error simulado de conexion")

    monkeypatch.setattr(db.session, "query", mock_query)

    resultado = HistoricDAO.obtener_id_estacion_por_str("EST01")

    assert resultado == []


def test_define_horas_pico_returns_extreme_rows(app):
    _, provincia, estacion = create_historico_entities()
    inicio = datetime(2026, 1, 1, 0, 0, 0)
    create_medicion(estacion, provincia, inicio + timedelta(hours=1), temperatura=30.0, humedad=20.0)
    create_medicion(estacion, provincia, inicio + timedelta(hours=2), temperatura=10.0, humedad=80.0)
    create_medicion(estacion, provincia, inicio + timedelta(hours=3), temperatura=20.0, humedad=40.0)

    resultado = HistoricDAO.define_horas_pico(estacion.id, provincia.id, inicio, inicio + timedelta(days=1))

    assert resultado["hora_temp_max"]._mapping["estacion_id"] == estacion.id
    assert resultado["hora_temp_min"]._mapping["estacion_id"] == estacion.id
    assert resultado["hora_humedad_max"]._mapping["estacion_id"] == estacion.id
    assert resultado["hora_humedad_min"]._mapping["estacion_id"] == estacion.id


def test_obtener_estaciones_usadas_returns_codes(app):
    _, provincia, estacion = create_historico_entities()
    inicio = datetime(2026, 1, 1, 0, 0, 0)
    create_medicion(estacion, provincia, inicio, temperatura=20.0, humedad=40.0)

    resultado = HistoricDAO.obtener_estaciones_usadas(provincia.id, inicio, inicio + timedelta(days=1))

    assert resultado == [estacion.codigo]


def test_define_computing_fechas_returns_none_when_no_data(app):
    inicio = datetime(2026, 1, 1, 0, 0, 0)

    resultado = HistoricDAO.define_computing_fechas(inicio, inicio + timedelta(days=1))

    assert resultado is None


def test_define_computing_fechas_returns_temperatures_and_station_metadata(app):
    _, provincia, estacion = create_historico_entities()
    inicio = datetime(2026, 1, 1, 0, 0, 0)
    create_medicion(estacion, provincia, inicio, temperatura=15.5, humedad=55.0)

    temperaturas, estaciones = HistoricDAO.define_computing_fechas(inicio, inicio + timedelta(days=1))

    assert temperaturas == [{"temperatura": 15.5}]
    assert estaciones == [{"codigo": estacion.codigo, "nombre": estacion.nombre}]


def test_define_computing_general_returns_none_when_no_data(app):
    inicio = datetime(2026, 1, 1, 0, 0, 0)

    resultado = HistoricDAO.define_computing_general(None, None, inicio, inicio + timedelta(days=1))

    assert resultado is None


def test_define_computing_general_returns_row_when_data_exists(app):
    _, provincia, estacion = create_historico_entities()
    inicio = datetime(2026, 1, 1, 0, 0, 0)
    medicion = create_medicion(estacion, provincia, inicio, temperatura=18.0, humedad=30.0)

    resultado = HistoricDAO.define_computing_general(None, None, inicio, inicio + timedelta(days=1))

    assert resultado._mapping["id"] == medicion.id
    assert resultado._mapping["timestamp"] == medicion.timestamp


def test_define_computing_data_dia_with_estacion_id_includes_station(app):
    _, provincia, estacion = create_historico_entities()
    inicio = datetime(2026, 1, 1, 0, 0, 0)
    create_medicion(estacion, provincia, inicio, temperatura=21.0, humedad=45.0)

    resultado = HistoricDAO.define_computing_data_dia(estacion.id, None, inicio, inicio)

    assert resultado["valores_diarios"][0]["estacion"] == estacion.codigo
    assert resultado["horas_pico"]["hora_temp_max"]._mapping["estacion_id"] == estacion.id


def test_define_computing_data_dia_with_provincia_id_includes_estaciones_usadas(app):
    _, provincia, estacion = create_historico_entities()
    inicio = datetime(2026, 1, 1, 0, 0, 0)
    create_medicion(estacion, provincia, inicio, temperatura=22.0, humedad=35.0)

    resultado = HistoricDAO.define_computing_data_dia(None, provincia.id, inicio, inicio)

    assert resultado["estaciones_usadas"] == [estacion.codigo]
    assert "valores_diarios" in resultado
    assert resultado["horas_pico"]["hora_temp_min"]._mapping["estacion_id"] == estacion.id


def test_define_computing_data_hora_with_estacion_id_uses_functor(monkeypatch):
    def fake_horas_pico(*args, **kwargs):
        return {"hora_temp_max": None}

    monkeypatch.setattr(HistoricDAO, "define_horas_pico", fake_horas_pico)
    monkeypatch.setattr(
        db.session,
        "execute",
        lambda *args, **kwargs: DummyResult([DummyRow({
            "hora": "12:00:00",
            "temp_media": 20.0,
            "humedad_media": 40.0,
            "vel_viento": 5.0,
            "precipitacion": 0.0,
            "radiacion": 10.0,
            "estacion": "EST01",
            "provincia": "CC",
            "fecha": datetime(2026, 1, 1, 12, 0, 0),
        })])
    )

    resultado = HistoricDAO.define_computing_data_hora(1, None, datetime(2026, 1, 1), datetime(2026, 1, 1))

    assert resultado["valores_horarios"] == [{
        "hora": "12:00:00",
        "temp_media": 20.0,
        "humedad_media": 40.0,
        "vel_viento": 5.0,
        "precipitacion": 0.0,
        "radiacion": 10.0,
        "estacion": "EST01",
        "provincia": "CC",
        "fecha": "2026-01-01T12:00:00",
    }]
    assert resultado["horas_pico"] == {"hora_temp_max": None}


def test_define_computing_data_hora_with_provincia_id_calls_estaciones_usadas(monkeypatch):
    called = {"used": False}

    def fake_horas_pico(*args, **kwargs):
        return {"hora_temp_max": None}

    def fake_estaciones_usadas(provincia_id, fec_init, fec_fin):
        called["used"] = True
        return ["EST01"]

    monkeypatch.setattr(HistoricDAO, "define_horas_pico", fake_horas_pico)
    monkeypatch.setattr(HistoricDAO, "obtener_estaciones_usadas", fake_estaciones_usadas)
    monkeypatch.setattr(
        db.session,
        "execute",
        lambda *args, **kwargs: DummyResult([DummyRow({
            "hora": "12:00:00",
            "temp_media": 20.0,
            "humedad_media": 40.0,
            "vel_viento": 5.0,
            "precipitacion": 0.0,
            "radiacion": 10.0,
            "estacion": None,
            "provincia": "CC",
            "fecha": datetime(2026, 1, 1, 12, 0, 0),
        })])
    )

    resultado = HistoricDAO.define_computing_data_hora(None, 1, datetime(2026, 1, 1), datetime(2026, 1, 1))

    assert called["used"] is True
    assert resultado["horas_pico"] == {"hora_temp_max": None}


def test_define_computing_data_semana_with_estacion_id_returns_valores_semanales(monkeypatch):
    monkeypatch.setattr(HistoricDAO, "define_horas_pico", lambda *args, **kwargs: {"hora_temp_max": None})
    monkeypatch.setattr(
        db.session,
        "execute",
        lambda *args, **kwargs: DummyResult([DummyRow({
            "anio": 2026,
            "semana": 1,
            "temp_media": 20.0,
            "temp_max": 25.0,
            "temp_min": 15.0,
            "humedad_media": 40.0,
            "humedad_max": 50.0,
            "humedad_min": 30.0,
            "vel_viento": 5.0,
            "vel_viento_max": 7.0,
            "precipitacion": 0.0,
            "etp_mon": 1.1,
            "pep_mon": 1.2,
            "radiacion": 10.0,
            "estacion": "EST01",
            "provincia": "CC",
        })])
    )

    resultado = HistoricDAO.define_computing_data_semana(1, None, datetime(2026, 1, 1), datetime(2026, 1, 1))

    assert resultado["valores_semanales"][0]["estacion"] == "EST01"
    assert resultado["horas_pico"] == {"hora_temp_max": None}


def test_define_computing_data_semana_with_provincia_id_includes_estaciones_usadas(monkeypatch):
    called = {"used": False}

    def fake_estaciones_usadas(provincia_id, fec_init, fec_fin):
        called["used"] = True
        return ["EST01"]

    monkeypatch.setattr(HistoricDAO, "define_horas_pico", lambda *args, **kwargs: {"hora_temp_max": None})
    monkeypatch.setattr(HistoricDAO, "obtener_estaciones_usadas", fake_estaciones_usadas)
    monkeypatch.setattr(
        db.session,
        "execute",
        lambda *args, **kwargs: DummyResult([DummyRow({
            "anio": 2026,
            "semana": 1,
            "temp_media": 20.0,
            "temp_max": 25.0,
            "temp_min": 15.0,
            "humedad_media": 40.0,
            "humedad_max": 50.0,
            "humedad_min": 30.0,
            "vel_viento": 5.0,
            "vel_viento_max": 7.0,
            "precipitacion": 0.0,
            "etp_mon": 1.1,
            "pep_mon": 1.2,
            "radiacion": 10.0,
            "estacion": None,
            "provincia": "CC",
        })])
    )

    resultado = HistoricDAO.define_computing_data_semana(None, 1, datetime(2026, 1, 1), datetime(2026, 1, 1))

    assert called["used"] is True
    assert resultado["valores_semanales"][0]["provincia"] == "CC"
    assert resultado["horas_pico"] == {"hora_temp_max": None}


def test_define_compution_data_mes_with_estacion_id_returns_valores_meses(monkeypatch):
    monkeypatch.setattr(HistoricDAO, "define_horas_pico", lambda *args, **kwargs: {"hora_temp_max": None})
    monkeypatch.setattr(
        db.session,
        "execute",
        lambda *args, **kwargs: DummyResult([DummyRow({
            "anio": 2026,
            "mes": 1,
            "temp_media": 20.0,
            "temp_max": 25.0,
            "temp_min": 15.0,
            "humedad_media": 40.0,
            "humedad_max": 50.0,
            "humedad_min": 30.0,
            "vel_viento": 5.0,
            "precipitacion": 0.0,
            "etp_mon": 1.1,
            "pep_mon": 1.2,
            "radiacion": 10.0,
            "estacion": "EST01",
            "provincia": "CC",
        })])
    )

    resultado = HistoricDAO.define_compution_data_mes(1, None, datetime(2026, 1, 1), datetime(2026, 1, 1))

    assert resultado["valores_diarios"][0]["estacion"] == "EST01"
    assert resultado["horas_pico"] == {"hora_temp_max": None}


def test_define_compution_data_mes_with_provincia_id_returns_valores_meses(monkeypatch):
    called = {"used": False}

    def fake_estaciones_usadas(provincia_id, fec_init, fec_fin):
        called["used"] = True
        return ["EST01"]

    monkeypatch.setattr(HistoricDAO, "define_horas_pico", lambda *args, **kwargs: {"hora_temp_max": None})
    monkeypatch.setattr(HistoricDAO, "obtener_estaciones_usadas", fake_estaciones_usadas)
    monkeypatch.setattr(
        db.session,
        "execute",
        lambda *args, **kwargs: DummyResult([DummyRow({
            "anio": 2026,
            "mes": 1,
            "temp_media": 20.0,
            "temp_max": 25.0,
            "temp_min": 15.0,
            "humedad_media": 40.0,
            "humedad_max": 50.0,
            "humedad_min": 30.0,
            "vel_viento": 5.0,
            "precipitacion": 0.0,
            "etp_mon": 1.1,
            "pep_mon": 1.2,
            "radiacion": 10.0,
            "estacion": "EST01",
            "provincia": "CC",
        })])
    )

    resultado = HistoricDAO.define_compution_data_mes(None, 1, datetime(2026, 1, 1), datetime(2026, 1, 1))

    assert called["used"] is True
    assert resultado["valores_diarios"][0]["provincia"] == "CC"
    assert resultado["horas_pico"] == {"hora_temp_max": None}


def test_historic_dao_methods_exception_paths_return_expected_defaults(app, monkeypatch):
    def mock_execute(*args, **kwargs):
        raise Exception("Error simulado de conexion")

    monkeypatch.setattr(db.session, "execute", mock_execute)

    assert HistoricDAO.obtener_estaciones_usadas(1, datetime(2026, 1, 1), datetime(2026, 1, 2)) == []
    assert HistoricDAO.define_computing_fechas(datetime(2026, 1, 1), datetime(2026, 1, 2)) is None
    assert HistoricDAO.define_computing_general(None, None, datetime(2026, 1, 1), datetime(2026, 1, 2)) == []
    assert HistoricDAO.define_computing_data_hora(None, None, datetime(2026, 1, 1), datetime(2026, 1, 2)) == []
    assert HistoricDAO.define_computing_data_dia(None, None, datetime(2026, 1, 1), datetime(2026, 1, 2)) == []
    assert HistoricDAO.define_computing_data_semana(None, None, datetime(2026, 1, 1), datetime(2026, 1, 2)) == []
    assert HistoricDAO.define_compution_data_mes(None, None, datetime(2026, 1, 1), datetime(2026, 1, 2)) == []