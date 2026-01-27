# Controlador CALENDARIO
from .plagas_service import PlagasService
from app.globals.convertidor_tipo import convertir_tipo
from . import calendario_bp
from flask import request, jsonify
from ..globals.log_decorator import log
from app.globals.dto2dict import dataclass_to_json
from helpers.ApiExceptions import APIException
from .plagas_dto import GrupoPlaga
import logging

logger = logging.getLogger(__name__)

@calendario_bp.route('/climate/plagas', methods = ['GET'])
@log('../logs/fichero_salida.json')
def calendario_plagas():

    try:
        cultivo = request.args.get('cultivo', 1)
        grupo = request.args.get('grupo', 'CEREALES')
        tipo = request.args.get('tipo', 'plaga')

        if not (cultivo or grupo):
            raise APIException(
                message = "Debe de indicarse al menos uno de los dos parámetros: cultivo | grupo",
                status = 400,
                errro = 'Invalid parameters'
            )
        
        # Conversor de string a GrupoPlaga
        type_grupo_plaga = convertir_tipo(grupo, GrupoPlaga)

        datos = PlagasService.get_plagas(tipo = tipo)

        logger.info(f"Datos recibidos por el servicio: {datos}")

        if not datos:
            raise APIException(
                message = "No se han encontrado datos para los parámetros especificados",
                status = 404,
                error = 'Data Not Found'
            )
        
        return dataclass_to_json(datos)
    
    except APIException as e:
        logger.error(f"API Exception: {e}")
        return jsonify(
            {
                'success' : 'false',
                'code' : '502',
                'message' : 'Provider Exception',
                'error' : str(e)
            }
        ), 502

