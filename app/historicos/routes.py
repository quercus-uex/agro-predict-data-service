# Controlador de HISTORICOS
from ..decorator.log_decorator import log
from flask import request, current_app
from helpers.ApiExceptions import APIException
from app.historicos.historico_service import HistoricService
from flask import jsonify, Blueprint
from ..globals.dto2dict import dataclass_to_json
from .historico_dto import TipoHistorico
from ..ingesta.ingesta_dto import ProcesoIngestaDTO
from .tasks import procesar_cola_pendientes_task
from app.globals.convertidor_tipo import convertir_tipo
from datetime import datetime
import logging

historic_bp = Blueprint('historico', __name__)
logger = logging.getLogger(__name__)

@historic_bp.route('/climate/historical/provincias', methods = ['GET'])
@log('../logs/fichero_salida.json')
def historicalProvincial():

    try: 
        province_code = request.args.get('provinceCode')
        type = request.args.get('type')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
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
            codigo_estacion = None
        ) 

        logger.info(f"Datos recibidos por el servicio: {datos}")

        if not datos:
            raise APIException(
                message = f'Los datos históricos de la provincia {province_code} para las fechas {start_date} -> {end_date} no se encuentran disponibles',
                status = 404,
                error = 'Data Not Found'
            )
        
        response = dataclass_to_json(datos)

        if isinstance(datos, ProcesoIngestaDTO):
            if datos.status == "FAILED":

                error_to_status = {
                    'BAD_REQUEST': 400,
                    'FORBIDDEN': 403,
                }
        
                status_code = error_to_status.get(datos.error, 500)
                return response, status_code
            return response, 200
        
        # Añado configuración en el header para que se descargue la respuesta en un fichero local sobre el usuario
        download = request.args.get('download', 'false').lower() == 'true'
        if download:
            response.headers["Content-Disposition"] = f"attachment; filename = agropredict_estacion_{province_code}_{start_date}_{end_date}.json"

        return response
    
    except APIException as e:
        logger.error(f"API Exception: {e}")
        return jsonify(
            {
                'success' : 'false',
                'code': str(e.status),
                'message' : e.message,
                'error': e.error
            }
        ), e.status
    
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
        
        if start_date > end_date:
            raise APIException(
                message = "La fecha inicial de recogida de datos no puede ser mayor a la fecha final",
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
            codigo_estacion = estacion_code_raw,
        )

        if not datos:
            raise APIException(
                message = f'Los datos históricos de la estacion {estacion_code} para las fechas {start_date} -> {end_date} no se encuentran disponibles',
                status = 404,
                error = 'Data Not Found'
            )

        response = dataclass_to_json(datos)
        if isinstance(datos, ProcesoIngestaDTO):
            if datos.status == "FAILED":

                error_to_status = {
                    'BAD_REQUEST': 400,
                    'FORBIDDEN': 403,
                }
        
                status_code = error_to_status.get(datos.error, 500)
                return response, status_code
            return response, 200
        # Añado configuración en el header para que se descargue la respuesta en un fichero local sobre el usuario
        download = request.args.get('download', 'false').lower() == 'true'
        if download:
            response.headers["Content-Disposition"] = f"attachment; filename = agropredict_estacion_{estacion_code}_{start_date}_{end_date}.json"
        
        return response
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return jsonify({
            'success' : 'false',
            'code' : str(400),
            'message' : 'Error al convertir el tipo',
            'error' : str(e)
        }), 400
    
    except APIException as e:
        logger.error(f"API Exception: {e}")
        return jsonify(
            {
                'success' : 'false',
                'code': str(e.status),
                'message' : e.message,
                'error': str(e)
            }
        ), e.status

@historic_bp.route('/climate/historical/reintentar-pendientes', methods=['POST'])
def reintentar_pendientes():
    task = procesar_cola_pendientes_task.delay()
    return jsonify({
        'task_id' : task.id,
        'status' : 'PROCESSING'
    }), 202