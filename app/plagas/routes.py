# Controlador CALENDARIO
from .plagas_service import PlagasService
from . import calendario_bp
from flask import request, jsonify
from ..decorator.log_decorator import log
from app.globals.dto2dict import dataclass_to_json
from helpers.ApiExceptions import APIException
from .plagas_dto import GrupoPlaga
import logging

logger = logging.getLogger(__name__)


@calendario_bp.route('/climate/plagas', methods=['POST'])
@log('../logs/fichero_salida.json')
def post_plaga():
    
    datos = request.get_json(silent = True)

    if not datos:
        raise APIException(
            status=400,
            message="Invalid body data",
            error="BAD_REQUEST"
        )

    PlagasService.registrar_plaga(
        public_id=datos['public_id'],
        nombre=datos['nombre'],
        agente_causante=datos['agente_causante'],
        momento_critico=datos['momento_critico'],
        observaciones=datos.get('observaciones'),
        mas_info=datos.get('mas_info'),
        tipo=datos['tipo'],
        grupo=datos['grupo'],
        recursos=datos['recursos']
    )

    return jsonify({
        'success': True,
        'status': 201,
        'message': 'Plaga insertada correctamente'
    }), 201


@calendario_bp.route('/climate/plagas', methods = ['GET'])
@log('../logs/fichero_salida.json')
def get_calendario_plagas():

    grupo = request.args.get('grupo')
    tipo = request.args.get('tipo')
    plaga_id = request.args.get('id') # Puede no existir 

    if not (tipo or grupo):
        raise APIException(
            status = 400,
            message = "Debe indicarse al menos uno de los parámetros: tipo | grupo",
            error = "INVALID_PARAMETERS" 
        )
    
    datos = PlagasService.get_plagas(
        grupo = grupo,
        tipo = tipo,
        plaga_id = plaga_id if plaga_id else None
    )

    if not datos:
        raise APIException(
            message = "No se han encontrado datos para los parámetros especificados",
            status = 404,
            error = 'DATA_NOT_FOUND'
        )
    
    return dataclass_to_json(datos)