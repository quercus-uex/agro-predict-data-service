from typing import Optional
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class ItacylService:
    _cliente = None

    @classmethod
    def _get_cliente(cls):
        """Lazy initialization: crea el cliente solo cuando se necesita"""
        if cls._cliente is None:
            from ..clients.itacyl_client import ItacylClient
            cls._cliente = ItacylClient(app=current_app)
        return cls._cliente

    @classmethod
    def get_itacyl_datos(
        cls,
        cultivo : Optional[int],
        grupo : Optional[str]
    ) :
        cliente = cls._get_cliente()
        datos = cliente.get_itacyl_data(
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