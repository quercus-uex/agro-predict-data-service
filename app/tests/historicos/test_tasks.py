import json
from app.historicos.tasks import programar_consulta_datos_task, procesar_cola_pendientes_task
from unittest.mock import patch, MagicMock
import pytest

def test_programar_consulta_datos_task_queues_correctly(mock_redis):
    args_prueba = {
        'tipo': 'Hora',
        'codigo_estacion_id': 'EST_01',
        'fec_init': '2026-01-01',
        'fec_fin': '2026-01-02'
    }
    
    # Ejecutamos la función directamente (sin trabajadores de Celery para entorno unitario)
    resultado = programar_consulta_datos_task(args_prueba)
    
    assert resultado["status"] == "QUEUED"
    
    # Verificamos que se guardó en nuestro Redis simulado
    redis_data = mock_redis.get(resultado["key"])
    assert redis_data is not None
    assert json.loads(redis_data)['tipo'] == 'Hora'

def test_error_programar_consulta_datos_tasks(mock_redis):
    args_prueba = {
        'tipo': 'Hora',
        'codigo_estacion_id': 'EST_01',
        'fec_init': '2026-01-01',
    }

    with pytest.raises(Exception):
        resultado = programar_consulta_datos_task(args_prueba)

def test_programar_consulta_datos_task_duplicate(mock_redis):
    args_prueba = {
        'tipo': 'Hora', 
        'codigo_estacion_id': 'EST_01', 
        'fec_init': '2026-01-01', 
        'fec_fin': '2026-01-02'
    }
    
    # Encolamos la primera vez
    programar_consulta_datos_task(args_prueba)
    # Encolamos la segunda vez la misma tarea
    resultado_duplicado = programar_consulta_datos_task(args_prueba)
    
    assert resultado_duplicado["status"] == "ALREADY_QUEUED"

@patch('app.historicos.tasks.SiarIngestionService.ingest_siar_data')
def test_successful_pending_queued_tasks(mock_ingest_siar_data, mock_redis):
    # simula una tarea pendiente en Redis
    task_key = "siar:pending:Hora:CC14:2025-01-01:2025-01-01"
    task_args = json.dumps({
        'tipo': 'HORA',
        'fec_init': '2026-01-01',
        'fec_fin':  '2026-01-01',
        'codigo_estacion_id':  'CC99',
        'codigo_provincia_id': None,
    })

    mock_redis.set(task_key, task_args)
    mock_ingest_siar_data.return_value = [MagicMock()]  # lista con datos → entra en el if

    resultado = procesar_cola_pendientes_task()

    assert len(resultado['ok'])      == 1
    assert len(resultado['failed'])  == 0
    assert len(resultado['skipped']) == 0
    assert mock_redis.get(task_key) is None  # verifica que se eliminó la tarea

def test_no_key_for_queued_tasks(mock_redis):
    resultado = procesar_cola_pendientes_task()

    assert resultado == {}

@patch('app.historicos.tasks.SiarIngestionService.ingest_siar_data')
def test_skip_process_task_queued(mock_ingest_siar_data, mock_redis):
    task1_key = "siar:pending:Hora:CC14:2025-01-01:2025-01-01"
    task1_args = json.dumps({
        'tipo': 'HORA',
        'fec_init': '2026-01-01',
        'fec_fin':  '2026-01-01',
        'codigo_estacion_id':  'CC99',
        'codigo_provincia_id': None,
    })
    task2_key = "siar:pending:Dia:CC14:2025-01-01:2025-01-01"
    task2_args = json.dumps({
        'tipo': 'Dia',
        'fec_init': '2026-01-01',
        'fec_fin':  '2026-01-01',
        'codigo_estacion_id':  'CC99',
        'codigo_provincia_id': None,
    })

    mock_redis.set(task1_key, task1_args)
    mock_redis.set(task2_key, task2_args)

    mock_ingest_siar_data.return_value = []

    resultado = procesar_cola_pendientes_task()
    print(resultado)
    assert len(resultado['skipped']) == 2