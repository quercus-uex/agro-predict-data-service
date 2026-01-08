# Controlador de HISTORICOS
from . import historic_bp
from ..globals.log_decorator import log
from flask import request
from helpers.ApiExceptions import APIException
from app.historicos.historico_service import HistoricService
from helpers.convertidor_tipo import convertir_tipo
from flask import jsonify
from ..globals.dto2dict import dataclass_to_json
import logging
import json

logger = logging.getLogger(__name__)

@historic_bp.route('/climate/historical/provincias')
@log('../logs/fichero_salida.json')
def historicalProvincial():

    try: 
        province_code = request.args.get('provinceCode', 1)
        type = request.args.get('type', 'HORA')
        start_date = request.args.get('startDate', '2025-12-31')
        end_date = request.args.get('endDate', '2025-12-31')

        if not all([province_code, type, start_date, end_date]):
            raise APIException(
                message = "Todos los parámetros deben de estar definidos",
                status = 400,
                error = 'Invalid parameters'
            )

        # Conversión de string a entero
        province_code = convertir_tipo(province_code, 'int')
        type_historico = convertir_tipo(type, 'tipo_historico')
        logger.info(f"Codigo de provincia: {province_code}")
       
        datos = HistoricService.get_historico(
            tipo = type_historico,
            fec_init = start_date,
            fec_fin = end_date,
            provincia_id = province_code,
            estacion_id = None
        ) 

        logger.info(f"Datos recibidos por el servicio: {datos}")

        if not datos:
            raise APIException(
                message = f'Los datos históricos de la provincia {province_code} para las fechas {start_date} -> {end_date} no se encuentran disponibles',
                status = 404,
                error = 'Data Not Found'
            )
        
        return dataclass_to_json(datos)
    
    except APIException as e:
        logger.error(f"API Exception: {e}")
        return jsonify(
            {
                'success' : 'false',
                'code': '502',
                'message' : 'Provider Exception',
                'error': str(e)
            }
        ), 502