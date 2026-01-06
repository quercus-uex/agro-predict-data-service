from clients.siar_client import SiARClient
from typing import Optional
from datetime import date
from historicos.historico_dto import TipoHistorico
from dateutil.parser import isoparse as parse_iso
class SiARService:

    @staticmethod
    def get_siar_data(
        estacion_id: Optional[str],
        provincia_id: Optional[str],
        tipo: TipoHistorico,
        fec_init: date,
        fec_fin: date
    ): 
        datos = SiARClient.get_historical_data_by_date(
            estacion_id = estacion_id,
            provincia_id = provincia_id,
            tipo = tipo,
            fec_init = fec_init,
            fec_fin = fec_fin
        )
        
        lista_datos = []
        for dato in datos:
            lista_datos.append(
                {
                    "timestamp" : parse_iso(dato.get('Fecha')),
                    "temperatura" : dato.get("TempMedia"),
                    "humedad" : dato.get("HumedadMedia"),
                    "vel_viento" : dato.get("VelViento"),
                    "precipitacion" : dato.get("Precipitacion"),
                    "etp_mon" : dato.get("EtPMon"),
                    "pep_mon" : dato.get("PePMon")
                }
            )

        return lista_datos

    def get_siar_informacion(
        estaciones : bool = True
    ):
        datos = SiARClient.get_informacion(
            estaciones = estaciones
        )

        lista_datos = []
        for dato in datos:
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
            else:
                lista_datos.append(
                    {
                        "nombre" : dato.get('Provincia'),
                        "codigo" : dato.get('Codigo'),
                        "codigo_ccaa" : dato.get('Codigo_CCAA')
                    }
                )