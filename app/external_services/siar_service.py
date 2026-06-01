from typing import Optional
from flask import current_app
from datetime import date, timedelta
from dateutil.parser import isoparse as parse_iso
from helpers.siar_exceptions import *
import logging
import time

logger = logging.getLogger(__name__)

class SiARService:

    _cliente = None

    @classmethod
    def _get_cliente(cls):
        """Lazy initialization: crea el cliente solo cuando se necesita"""
        if cls._cliente is None:
            from ..clients.siar_client import SiARClient
            cls._cliente = SiARClient(app=current_app)
        return cls._cliente

    @classmethod
    def get_siar_data(
        cls,
        estacion_id: Optional[str],
        provincia_id: Optional[str],
        tipo,
        fec_init: date,
        fec_fin: date,
        on_datos_obtenidos: Optional[callable] = None
    ): 
        cliente = cls._get_cliente()
        lista_datos = []
        cursor = fec_init
        contador_timeouts = 0
        contador_peticiones = 0
        while cursor <= fec_fin:
            
            datos = cliente.get_historical_data_by_date(
                estacion_id=estacion_id,
                provincia_id=provincia_id,
                tipo=tipo,
                fec_init=cursor,
                fec_fin=cursor
            )

            if not isinstance(datos, list):
                if datos.get('success') == False:
                    message = datos.get('message', '')
                    if "inferior a" in message: 
                        raise SiARFechaInvalidaError(
                            message = "La Fecha Inicial de consulta proporcionada es inferior a la Fecha Mínima Inicial autorizada",
                            status = 400,
                            error = "BAD_REQUEST"
                        )
                    
                    if "autenticación" in message.lower() or "clave API" in message.lower():
                        logger.warning(f"Rate limit alcanzado para {cursor}, esperando 62s...")
                        time.sleep(62)
                        contador_peticiones = 0  # reset tras la espera
                        continue  # reintenta el mismo día
                    
                    time.sleep(62)
                    contador_timeouts += 1
                    if contador_timeouts >= 2:
                        raise SiARLimiteDiarioError(
                            message = "Has consultado el límite máximo de datos diario por SiAR, intentalo de nuevo mañana",
                            status = 403,
                            error = "FORBIDDEN"
                            
                        )
                    # No avanzamos el cursor: reintentamos el mismo día tras el sleep
                    continue 

            else:
                datos_dia = []
                for dato in (datos or []):
                    datos_dia.append({
                        "timestamp": parse_iso(dato.get('Fecha')),
                        "temperatura": dato.get("TempMedia"),
                        "humedad": dato.get("HumedadMedia"),
                        "vel_viento": dato.get("VelViento"),
                        "precipitacion": dato.get("Precipitacion"),
                        "etp_mon": dato.get("EtPMon"),
                        "pep_mon": dato.get("PePMon"),
                        "estacion": dato.get("Estacion"),
                        "radiacion": dato.get("Radiacion"),
                    })

                if datos_dia:
                    lista_datos.extend(datos_dia)
                    if on_datos_obtenidos:
                        on_datos_obtenidos(datos_dia)

            cursor += timedelta(days=1)  # ← solo avanza si los datos fueron válidos
            contador_peticiones += 1
            if contador_peticiones % 5 == 0: # Máximo número de peticiones por minuto a SiAR
                logger.info(f"Límite de 5 peticiones alcanzado, esperando 62s...")
                time.sleep(62)
        return lista_datos

    @classmethod
    def get_siar_informacion(
        cls,
        estaciones : bool = True
    ):
        cliente = cls._get_cliente()
        datos = cliente.get_informacion(
            estaciones = estaciones
        )

        lista_datos = []
        # Insertamos en la lista, datos necesarios para la comunidad autonoma
        for dato in datos:
            # Si se especifica en la peticion, insertamos en la lista datos de estaciones
            if estaciones: 
                lista_datos.append(
                    {
                        "nombre_estacion" : dato.get('Estacion'),
                        "codigo" : dato.get('Codigo'),
                        "longitud" : dato.get('Longitud'),
                        "latitud" : dato.get('Latitud'),
                        "altitud" : dato.get('Altitud')
                    }
                )
            # Insertamos en la lista, datos necesarios para las provincias
            else: 
                lista_datos.append(
                    {
                        "nombre-comunidades": [
                            "ANDALUCIA",
                            "ARAGON",
                            "ASTURIAS",
                            "BALEARES",
                            "CASTILLA Y LEON",
                            "CASTILLA LA MANCHA",
                            "CANARIAS",
                            "CATALUNIA",
                            "CEUTA",
                            "EXTREMADURA",
                            "GALICIA",
                            "MADRID",
                            "MELILLA",
                            "MURCIA",
                            "PVASCO",
                            "RIOJA",
                            "CANTABRIA",
                            "VALENCIA",
                        ]
                    }
                )
                lista_datos.append(
                    {
                        "nombre" : dato.get('Provincia'),
                        "codigo" : dato.get('Codigo'),
                        "codigo_ccaa" : dato.get('Codigo_CCAA')
                    }
                )
        return lista_datos