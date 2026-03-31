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


@calendario_bp.route('/climate/plagas', methods = ['POST'])
@log('../logs/fichero_salida.json')
def post_plaga():
    try:
        datos = request.get_json()

        if not datos:
            return jsonify(
                {
                    'success' : 'false',
                    'code' : '400',
                    'message' : 'Invalid body data',
                    'error' : 'Debe introducirse un payload de datos sobre esta petición'
                }
            ), 400
        
        # Creo una nueva plaga y la almaceno en BD
        plaga = PlagasService.registrar_plaga(
            public_id = datos['public_id'],
            nombre = datos['nombre'],
            agente_causante = datos['agente_causante'],
            momento_critico = datos['momento_critico'],
            observaciones = datos.get('observaciones', ''),
            mas_info = datos.get('mas_info', ''),
            tipo = datos['tipo']
        )

        if not plaga:
            return jsonify(
                {
                    'success' : 'false',
                    'status' : '404',
                    'meesage' : 'Bad Request'
                }
            )

        return jsonify({
            'success' : 'true',
            'status' : '201',
            'message' : 'Plaga insertada correctamente',
        }), 201
    
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

@calendario_bp.route('/climate/plagas', methods = ['GET'])
@log('../logs/fichero_salida.json')
def get_calendario_plagas():

    try:
        grupo = request.args.get('grupo')
        tipo = request.args.get('tipo')
        plaga_id = request.args.get('id') # Piede no existir 

        print(f"Grupo - Tipo : {grupo} - {tipo}")
        if not (tipo or grupo):
            return jsonify({
                'success': 'false',
                'code': '400',
                'message': 'Invalid parameters',
                'error': 'Debe indicarse al menos uno de los parámetros: tipo | grupo'
            }), 400
        
        datos = PlagasService.get_plagas(
            tipo = tipo,
            plaga_id = plaga_id if plaga_id else None
        )

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

