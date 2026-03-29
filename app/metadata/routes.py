from .metadata_service import MetadataService
from . import metadata_bp
from flask import jsonify, request
from werkzeug.utils import secure_filename
from ..globals.log_decorator import log
from helpers.ApiExceptions import APIException
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