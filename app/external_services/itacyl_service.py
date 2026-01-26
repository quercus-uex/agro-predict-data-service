from ..clients.itacyl_client import ItacylClient
from app import create_app
from typing import Optional
import logging
import json

logger = logging.getLogger(__name__)

class ItacylService:
    app = create_app()
    client = ItacylClient(app)

    @staticmethod
    def get_itacyl_datos(
        cultivo : Optional[int],
        grupo : Optional[str]
    ) :
        datos = ItacylService.client.get_itacyl_data(
            cultivo = cultivo,
            grupo = grupo
        )

        lista_datos = []

        for d in datos:
            lista_datos.append(
                {
                    "id" : d.get('id'),
                    "nombre" : d.get('name'),
                    "agente_causante" : d.get('causalAgent'),
                    "momento_critico" : d.get('criticalMoment'),
                    "observaciones" : d.get('observations'),
                    "enlace" : d.get('link'),
                    "tipo" : d.get('type'),
                    "calendario_de_productos" : d.get('productCalendar')
                }
            )

        return lista_datos