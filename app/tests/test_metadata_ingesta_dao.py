from datetime import datetime
from unittest.mock import MagicMock

import pytest
from app.extensions import db
from app.ingesta.ingesta_dao import IngestaDAO
from app.metadata.metadata_dao import MetadataDAO
from app.models import Dispositivos, Sensores, Metadatos, IngestaStatus, Provincia


def create_device_and_sensor(app):
    dispositivo = Dispositivos(id="1", public_id="dev1", dev_eui="EUI123", descripcion="desc", nombre="Device", creado=datetime.now())
    db.session.add(dispositivo)
    db.session.commit()

    sensor = Sensores(eui="sensor-01", dispositivo_id=dispositivo.dev_eui)
    db.session.add(sensor)
    db.session.commit()
    return dispositivo, sensor


def create_provincia(app):
    provincia = Provincia(codigo="XX", nombre="Prueba", ccaa_id=1)
    db.session.add(provincia)
    db.session.commit()
    return provincia


def test_metadata_dao_consultar_registro_returns_inserted_row(app):
    provincia = create_provincia(app)
    resultados = MetadataDAO.consultar_registro(Provincia, {"codigo": provincia.codigo})

    assert isinstance(resultados, list)
    assert resultados[0]["codigo"] == provincia.codigo


def test_metadata_dao_actualizar_y_eliminar_registro(app):
    provincia = create_provincia(app)
    count = MetadataDAO.actualizar_registro(Provincia, {"nombre": "Cambio"}, [Provincia.codigo == provincia.codigo])
    assert count == 1

    resultados = MetadataDAO.consultar_registro(Provincia, {"codigo": provincia.codigo})
    assert resultados[0]["nombre"] == "Cambio"

    removed = MetadataDAO.eliminar_registro(Provincia, [Provincia.codigo == provincia.codigo])
    assert removed == 1


def test_metadata_dao_crear_registro_with_dispositivo_dependency(app):
    dispositivo, sensor = create_device_and_sensor(app)

    entidad = MetadataDAO.crear_registro(
        Sensores,
        {"eui": "sensor-01", "dispositivo_id": dispositivo.dev_eui},
        ["eui"],
    )

    assert entidad is not None
    assert entidad.eui == "sensor-01"


def test_metadata_dao_validar_columnas_returns_column_names():
    columnas = MetadataDAO.vaidar_columnas(Provincia)
    assert "codigo" in columnas
    assert "nombre" in columnas


def test_metadata_dao_eliminar_registro_requires_filters(app):
    with app.app_context():
        with pytest.raises(ValueError, match="Se requieren filtros para eliminar registros"):
            MetadataDAO.eliminar_registro(Provincia, None)


def test_ingesta_dao_create_obtener_actualizar_delete(app):
    IngestaDAO.create(
        status="PENDING",
        dataset="actual_futuro",
        tipo="actual",
        year=2026,
        month=1,
        day=1,
        zona="nacional",
        started_at=datetime.now(),
        codigo="",
        finished_at=None,
        error_message=None,
    )

    estado = IngestaDAO.obtener_estado(
        dataset="actual_futuro",
        tipo="actual",
        year=2026,
        month=1,
        day=1,
        zona="nacional",
        codigo="",
        error=None,
    )

    assert estado is not None
    assert estado["status"] == "PENDING"

    IngestaDAO.actualizar_estado(
        status="READY",
        dataset="actual_futuro",
        tipo="actual",
        year=2026,
        month=1,
        day=1,
        zona="nacional",
        codigo="",
        finish_time=datetime.now(),
        error=None,
    )

    estado_actualizado = IngestaDAO.obtener_estado(
        dataset="actual_futuro",
        tipo="actual",
        year=2026,
        month=1,
        day=1,
        zona="nacional",
        codigo="",
        error=None,
    )

    assert estado_actualizado["status"] == "READY"

    IngestaDAO.delete_estado(
        dataset="actual_futuro",
        tipo="actual",
        year=2026,
        month=1,
        day=1,
        zona="nacional",
        codigo="",
    )

    estado_deleted = IngestaDAO.obtener_estado(
        dataset="actual_futuro",
        tipo="actual",
        year=2026,
        month=1,
        day=1,
        zona="nacional",
        codigo="",
        error=None,
    )
    assert estado_deleted is None
