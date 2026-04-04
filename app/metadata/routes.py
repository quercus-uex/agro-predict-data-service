from .metadata_service import MetadataService
from . import metadata_bp
from flask import jsonify, request
from werkzeug.utils import secure_filename
from ..decorator.log_decorator import log
from helpers.ApiExceptions import APIException
from ..globals.dto2dict import dataclass_to_json
import logging
import os

logger = logging.getLogger(__name__)

@metadata_bp.route('/metadatos/registro/<string:tipo>', methods = ['POST'])
@log('../logs/fichero_salida.json')
def almacenar_fichero(
    tipo : str
):
    
    def allowed_extensions(filename : str):
        if filename.rsplit('.', 1)[1].lower() != 'csv':
            return False
        return True

    try:
        if tipo.lower() not in ['parcelas', 'sensores', 'dispositivos']:
            return jsonify(
                {
                    'success' : 'false',
                    'code' : '400',
                    'message' : 'Invalid parameter',
                    'error' : 'Debe indicarse el tipo de metadato que se va a incluir (parcelas, sensores o dispositivos)'
                }
            ), 400
        
        if 'file' not in request.files:
            return jsonify(
                {
                    'success' : 'false',
                    'code' : '400',
                    'message' : 'Invalid parameter',
                    'error' : 'Se debe indicar un fichero en el cuerpo de la peticion'
                }
            ), 400
        
        fichero = request.files['file']

        if fichero.filename == '':
            return jsonify(
                {
                    'success' : 'false',
                    'code' : '400',
                    'message' : 'Invalid parameter',
                    'error' : 'Se debe indicar un fichero en el cuerpo de la peticion'
                }
            ), 400
        
        if fichero and allowed_extensions(fichero.filename):
            nombre_fichero = secure_filename(fichero.filename)
            if not MetadataService.comprobar_existencia_fichero(tipo, fichero):
                ruta_almacenar = MetadataService.obtener_ruta_metadatos(tipo.lower())
                fichero.save(os.path.join(ruta_almacenar, nombre_fichero))
                MetadataService.registrar_modelo(tipo, fichero.filename)
            else:
                return jsonify({
                    'success' : 'false',
                    'status' : '400',
                    'message' : 'Bad Request',
                    'error' : 'Fichero ya registrado en el sistema'
                }), 400
        else:
            return jsonify({
                'success' : 'false',
                'status' : '400',
                'message' : 'Bad Request',
                'error' : 'Fichero no proporcionado o extensión no permitida' 
            }), 400


        return jsonify({
            'success' : 'true',
            'status' : '201',
            'message' : 'Fichero con metadatos insertado correctamente'
        }), 201
    
    except APIException as e:
        logger.error(f"API Exception : {e}")
        return jsonify({
            'success' : 'false',
            'code' : '500',
            'message' : 'Internal Server Error',
            'error' : str(e)
        }), 500

@metadata_bp.route('/metadatos/<string:tipo>')
@log('../logs/fichero_salida.json')
def obtener_metadatos(
    tipo : str
):
    try:
        if tipo.lower() not in ['parcelas', 'sensores', 'dispositivos']:
            return jsonify(
                {
                    'success' : 'false',
                    'code' : '400',
                    'message' : 'Invalid Parameters',
                    'error' : 'El tipo de metadato consultado no es soportado'
                }
            )
        
        filtros = []

        entidad_id = request.args.get('entidad_id')

        if entidad_id:
            filtros.append({
                'entidad_id' : entidad_id,
            })
        
        datos = MetadataService.obtener_metadatos(tipo, filtros)

        if not datos:
            return jsonify(
                {
                    'success' : 'false',
                    'code' : '404',
                    'message' : 'Data Not Found',
                    'error' : f'No se han encontrado datos registrados sobre el tipo {tipo}'
                }
            )
        
        return dataclass_to_json(datos)
    
    except APIException as e:
        logger.error(f"API Exception : {e}")
        return jsonify(
            {
                'success' : 'false',
                'code' : '500',
                'message' : 'Internal Server Error',
                'error' : 'Error interno del servidor'
            }
        )



