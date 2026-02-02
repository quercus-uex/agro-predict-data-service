from .ingesta_service import IngestionService
import threading


def _ingesta_thread(
    app,
    codigo_estacion_id,
    codigo_provincia_id,
    tipo,
    fec_init,
    fec_fin
):
    with app.app_context():
        IngestionService.ingest_data(
            codigo_estacion_id = codigo_estacion_id,
            codigo_provincia_id = codigo_provincia_id,
            tipo = tipo,
            fec_init = fec_init,
            fec_fin = fec_fin
        )

def lanzar_ingesta_background(
    app,
    codigo_estacion_id ,
    codigo_provincia_id,
    tipo,
    fec_init,
    fec_fin
):
    """
    Configuración de hilo en segundo plano que 
    almacena datos solicitados en la base de datos
    """
    thread = threading.Thread(
        target = _ingesta_thread,
        args = (
            app,
            codigo_estacion_id,
            codigo_provincia_id,
            tipo,
            fec_init,
            fec_fin
        ),
        daemon = True
    )
    thread.start()