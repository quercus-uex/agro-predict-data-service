import threading
from app.ingesta.ingesta_service import IngestionService

def lanzar_ingesta_background(
    *args
):
    """
    Configuración de hilo en segundo plano que 
    almacena datos solicitados en la base de datos
    """
    thread = threading.Thread(
        target = IngestionService.ingest_data,
        args = args,
        daemon = True
    )
    thread.start()