"""
ingesta_service.py
==================
Punto de entrada único que delega en sub-servicios especializados.
Cada sub-servicio es responsable de UNA fuente de datos externa.
"""
from .siar_ingestion_service import SiarIngestionService
from .aemet_ingestion_service import AemetIngestionService
from .itacyl_ingestion_service import ItacylIngestionService
from .sensor_ingestion_service import SensorIngestionService
from .metadata_ingestion_service import MetadataIngestionService


# Re-exportamos la fachada pública para no romper imports existentes
class IngestionService(
    SiarIngestionService,
    AemetIngestionService,
    ItacylIngestionService,
    SensorIngestionService,
    MetadataIngestionService,
):
    """
    Hereda todos sus métodos estáticos sin añadir lógica propia.
    """
    pass