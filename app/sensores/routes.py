from .sensores_service import SensoresService
from flask import request, Blueprint
from ..decorator.log_decorator import log
from ..globals.convertidor_tipo import convertir_tipo
from app.globals.dto2dict import dataclass_to_json
from helpers.ApiExceptions import APIException
from datetime import date
import logging

sensores_bp = Blueprint('sensores', __name__)
logger = logging.getLogger(__name__)

@sensores_bp.route('/sensores', methods = ['GET'])
@log('../logs/fichero_salida.json')
def sensores():
    
    euis = request.args.getlist('eui')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    nombre_dt_agro = request.args.get('nombre_dt_agro', '')
    nombre_predictor = request.args.get('nombre_predictor', '')

    print(euis)

    if not all([euis, fecha_inicio, fecha_fin, nombre_dt_agro, nombre_predictor]):
        raise APIException(
            message = "Debe indicarse todos los parámetros de la query (eui, fecha_inicio, fecha_fin)",
            status = 400,
            error = 'Invalid parameters'
        )

    # Conversor de string a date
    fecha_inicio = convertir_tipo(fecha_inicio, date)
    fecha_fin = convertir_tipo(fecha_fin, date)

    datos = SensoresService.get_sensor_data(
        euis = euis,
        fecha_inicio     = fecha_inicio,
        fecha_fin        = fecha_fin,
        nombre_dtagro    = nombre_dt_agro,
        nombre_predictor = nombre_predictor
    )

    if not datos:
        raise APIException(
            message = "No se han encontrado datos de sensores para los parámetros indicados",
            status = 404,
            error = 'Data Not Found'
        )
    
    return dataclass_to_json(datos), 200