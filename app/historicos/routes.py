# Controlador de HISTORICOS
from . import historic_bp
from ..decorator.log_decorator import log
from ..decorator.token_decorator import token_required
from flask import request, current_app
from helpers.ApiExceptions import APIException
from app.historicos.historico_service import HistoricService
from flask import jsonify
from ..globals.dto2dict import dataclass_to_json
from .historico_dto import TipoHistorico
from app.globals.convertidor_tipo import convertir_tipo
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

@historic_bp.route('/climate/historical/provincias', methods = ['GET'])
@log('../logs/fichero_salida.json')
#@token_required(roles = ['public', 'data-reader'])
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
        
        # Conversión de tipos
        type_historico = convertir_tipo(type, TipoHistorico)
        start_date = convertir_tipo(start_date, datetime)
        end_date = convertir_tipo(end_date, datetime)
        print(start_date, flush = True)       

        datos = HistoricService.get_historico(
            current_app._get_current_object(),
            tipo = type_historico,
            fec_init = start_date,
            fec_fin = end_date,
            provincia_id = province_code,
            estacion_id = None,
            codigo_estacion = None
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
    
@historic_bp.route('/climate/historical/estacion', methods = ['GET'])
@log('../logs/fichero_salida.json')
def historicalEstacion():
    
    try:
        estacion_code_raw = request.args.get('estacionCode')
        type = request.args.get('type')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        if not all([estacion_code_raw, type, start_date, end_date]):
            raise APIException(
                message = "Todos los parámetros deben de estar definidos",
                status = 400,
                error = 'Invalid parameters'
            )
        
        estacion_code_format = estacion_code_raw[2:len(estacion_code_raw)]
        estacion_code = convertir_tipo(estacion_code_format, int)
        type_historico = convertir_tipo(type, TipoHistorico)
        start_date = convertir_tipo(start_date, datetime)
        end_date = convertir_tipo(end_date, datetime)

        datos = HistoricService.get_historico(
            current_app._get_current_object(),
            tipo = type_historico,
            fec_init = start_date,
            fec_fin = end_date,
            provincia_id = None,
            estacion_id = estacion_code,
            codigo_estacion = estacion_code_raw,
        )

        if not datos:
            raise APIException(
                message = f'Los datos históricos de la estacion {estacion_code} para las fechas {start_date} -> {end_date} no se encuentran disponibles',
                status = 404,
                error = 'Data Not Found'
            )
        
        
        response = dataclass_to_json(datos)
        # Añado configuración en el header para que se descargue la respuesta en un fichero local sobre el usuario
        if response.json.get('type'):
            response.headers["Content-Disposition"] = f"attachment; filename = agropredict_estacion_{estacion_code}_{start_date}_{end_date}.json"
        
        return response
    
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

