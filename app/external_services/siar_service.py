from typing import Optional
from flask import current_app
from datetime import date, timedelta
from dateutil.parser import isoparse as parse_iso
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
        # Necesito un cursor para almacenar datos faltantes para la peticiónm cada día del rango
        cursor = fec_init

        while cursor <= fec_fin:
            datos = cliente.get_historical_data_by_date(
                estacion_id = estacion_id,
                provincia_id = provincia_id,
                tipo = tipo,
                fec_init = cursor,
                fec_fin = cursor
            )
            print(f"DEBUG: siar {datos}")
            # Si devuelve un success = false quiere decir que se puede haber rebosado el límite
            contador_timeouts = 0 # Si supera un umbral, el límite es diario y no por minuto
            if not isinstance(datos, list):
                if datos.get('success') == False:
                    print('entro')
                    logger.warning('Limite por minuto de datos alcanzado')
                    time.sleep(62)
                    contador_timeouts +=1
                    if contador_timeouts >= 2:
                        return {
                            'success' : False,
                            'meesage': 'Has consultado el límite máximo de datos diario por SiAR, intentalo de nuevo mañana'
                        }       
            else:
                datos_dia = []
                for dato in (datos or []):
                    datos_dia.append(
                        {
                            "timestamp" : parse_iso(dato.get('Fecha')),
                            "temperatura" : dato.get("TempMedia"),
                            "humedad" : dato.get("HumedadMedia"),
                            "vel_viento" : dato.get("VelViento"),
                            "precipitacion" : dato.get("Precipitacion"),
                            "etp_mon" : dato.get("EtPMon"),
                            "pep_mon" : dato.get("PePMon"),
                            "estacion" : dato.get("Estacion"),
                            "radiacion" : dato.get("Radiacion"),
                        }
                    )
                
                if datos_dia:
                    lista_datos.extend(datos_dia)
                    if on_datos_obtenidos:
                        on_datos_obtenidos(datos_dia)

                cursor += timedelta(days=1)

        print(lista_datos)
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
                            "EXTREMADURA",
                            "ARAGON",
                            "ASTURIAS",
                            "BALEARES",
                            "CANARIAS",
                            "CANTABRIA",
                            "CASTILLA-LA MANCHA",
                            "CASTILLA Y LEON",
                            "CATALUNIA",
                            "MADRID",
                            "MURCIA",
                            "GALICIA",
                            "RIOJA",
                            "NAVARRA",
                            "PAIS VASCO"
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