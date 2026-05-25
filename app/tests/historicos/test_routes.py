from unittest.mock import patch, MagicMock
from helpers.ApiExceptions import APIException
from app.ingesta.ingesta_dto import ProcesoIngestaDTO
from datetime import datetime
import pytest

#---------------------------------
# HISTORICO PROVINCIA
#---------------------------------

def test_get_historical_provincias_missing_params(client):
    # No envío parámetros en la petición
    response = client.get('/climate/historical/provincias')
    assert response.status_code == 400

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_provincias_no_data(mock_get_historico, client):
    mock_get_historico.return_value = None

    response = client.get('/climate/historical/provincias?provinceCode=CC&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 404

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_provincias_data(mock_get_historico, client):
    mock_get_historico.return_value = MagicMock()

    response = client.get('/climate/historical/provincias?provinceCode=CC&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 200

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_provincias_download(mock_get_historico, client):
    mock_get_historico.return_value = MagicMock()

    response = client.get('/climate/historical/provincias?provinceCode=06&type=HORA&startDate=2026-01-01&endDate=2026-01-01&download=true')

    assert 'Content-Disposition' in response.headers
    assert "attachment;" in response.headers["Content-Disposition"]

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_provincias_failed_ingestion(mock_get_historico, client):
    mock_get_historico.return_value = ProcesoIngestaDTO(
        status = "FAILED",
        datos_solicitados = "test",
        started_at = datetime(2026, 1, 1, 0, 0),
        finished_at = datetime(2026, 1, 1, 0, 0),
        error = 'BAD_REQUEST' 
    )

    response = client.get('/climate/historical/provincias?provinceCode=CC&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 400
    assert response.json['error'] == 'BAD_REQUEST'

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_provincias_failed_ingest_status(mock_get_historico, client):
    mock_get_historico.return_value = ProcesoIngestaDTO(
        status = "FAILED",
        datos_solicitados = "test",
        started_at = datetime(2026, 1, 1, 0, 0),
        finished_at = datetime(2026, 1, 1, 0, 0),
        error = 'SERVER_ERROR'
    )

    response = client.get('/climate/historical/provincias?provinceCode=CC&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 500
    assert response.json['error'] == 'SERVER_ERROR'

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_provincias_success_ingest_status(mock_get_historico, client):
    mock_get_historico.return_value = ProcesoIngestaDTO(
        status = "READY",
        datos_solicitados = "test",
        started_at = datetime(2026, 1, 1, 0, 0),
        finished_at = datetime(2026, 1, 1, 0, 0),
        error = None
    )

    response = client.get('/climate/historical/provincias?provinceCode=CC&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 200

#---------------------------------
# HISTORICO ESTACION
#---------------------------------

@pytest.mark.parametrize("params,descripcion", [
    ("estacionCode=CC&type=HORA&startDate=no-es-fecha&endDate=2026-01-01", "startDate inválida"),
    ("estacionCode=CC&type=HORA&startDate=2026-01-01&endDate=no-es-fecha", "endDate inválida"),
    ("estacionCode=CC&type=TIPO_INVALIDO&startDate=2026-01-01&endDate=2026-01-01", "tipo inválido"),
    ("estacionCode=no-es-int&type=HORA&startDate=2026-01-01&endDate=2026-01-01", "estacion no es int"),
])
def test_get_historical_estacion_params_invalidos(client, params, descripcion):
    response = client.get(f'/climate/historical/estacion?{params}')
    assert response.status_code == 400, f"Falló con: {descripcion}"

def test_get_historical_estacion_no_params_defined(client):
    response = client.get('/climate/historical/estacion')
    assert response.status_code == 400

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_estaciones_no_data(mock_get_historico, client):
    mock_get_historico.return_value = None

    response = client.get('/climate/historical/estacion?estacionCode=CC01&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 404

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_estacion_data(mock_get_historico, client):
    mock_get_historico.return_value = MagicMock()

    response = client.get('/climate/historical/estacion?estacionCode=CC01&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 200

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_estaciones_download(mock_get_historico, client):
    mock_get_historico.return_value = MagicMock()

    response = client.get('/climate/historical/estacion?estacionCode=CC01&type=HORA&startDate=2026-01-01&endDate=2026-01-01&download=true')

    assert 'Content-Disposition' in response.headers
    assert "attachment;" in response.headers["Content-Disposition"]

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_estaciones_failed_ingestion(mock_get_historico, client):
    mock_get_historico.return_value = ProcesoIngestaDTO(
        status = "FAILED",
        datos_solicitados = "test",
        started_at = datetime(2026, 1, 1, 0, 0),
        finished_at = datetime(2026, 1, 1, 0, 0),
        error = 'BAD_REQUEST' 
    )

    response = client.get('/climate/historical/estacion?estacionCode=CC01&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 400
    assert response.json['error'] == 'BAD_REQUEST'

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_estaciones_failed_ingest_status(mock_get_historico, client):
    mock_get_historico.return_value = ProcesoIngestaDTO(
        status = "FAILED",
        datos_solicitados = "test",
        started_at = datetime(2026, 1, 1, 0, 0),
        finished_at = datetime(2026, 1, 1, 0, 0),
        error = 'SERVER_ERROR'
    )

    response = client.get('/climate/historical/estacion?estacionCode=CC01&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 500
    assert response.json['error'] == 'SERVER_ERROR'

@patch('app.historicos.routes.HistoricService.get_historico')
def test_get_historical_estaciones_success_ingest_status(mock_get_historico, client):
    mock_get_historico.return_value = ProcesoIngestaDTO(
        status = "READY",
        datos_solicitados = "test",
        started_at = datetime(2026, 1, 1, 0, 0),
        finished_at = datetime(2026, 1, 1, 0, 0),
        error = None
    )

    response = client.get('/climate/historical/estacion?estacionCode=CC01&type=HORA&startDate=2026-01-01&endDate=2026-01-01')

    assert response.status_code == 200

def test_retry_queued_tasks(client):
    mock_task = MagicMock()
    mock_task.id = "fake-task-id"

    with patch("app.historicos.routes.procesar_cola_pendientes_task.delay", return_value=mock_task):
        response = client.post('/climate/historical/reintentar-pendientes')
    
    assert response.status_code == 202

