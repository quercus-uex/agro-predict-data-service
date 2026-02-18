from . import cultivo_bp
from ..globals.log_decorator import log
from ..globals.dto2dict import dataclass_to_json
from helpers.ApiExceptions import APIException
from helpers.SuccessInsert import SuccessInsert
from .cultivos_service import CultivoService
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)


@cultivo_bp.route('/crop/variedades/<string:nombre>/umbrales', methods = ['GET', 'POST'])
@log('../logs/fichero_salida.json')
def umbrales_variedad(
    nombre : str
):
    try:
        if not nombre:
            raise APIException(
                message = 'Parametros de entrada incompletos',
                status = 400,
                error = 'Invalid Parameters'
            )
            
        if request.method == 'GET':
            
            datos = CultivoService.obtener_umbrales_variedad(
                nombre_variedad = nombre
            )

            if not datos:
                raise APIException(
                    message = f'Los umbrales para la variedad {nombre} no están definidos',
                    status = 404,
                    error = 'Data Not Found'
                )
            
            return dataclass_to_json(datos)
        
        elif request.method == 'POST':

            data = request.get_json()

            if not data:
                raise APIException(
                    message = 'Datos en json requeridos',
                    status = 400,
                    error = 'Bad Request'
                )
            
            CultivoService.registrar_umbral(
                nombre_variedad = nombre,
                args = data
            )

            return jsonify(
                {
                    'success': 'true',
                    'message': "Se ha creado correctame el umbral",
                    'status' : 201
                }
            ), 201
        
    except APIException as e:
        logger.info(f"API Exception : {e}")
        return jsonify(
            {
                'success' : 'false',
                'code' : '500',
                'message' : 'Internal Error',
                'error' : str(e)
            }
        ), 500
    

@cultivo_bp.route('/crop/variedades/<string:nombre>/horas_frio', methods = ['GET', 'PATCH'])
@log('../logs/fichero_salida.json')
def horas_frio_variedad(
    nombre : str
):
    try:
        if not nombre:
            raise APIException(
                message = 'Parametros de entrada incompletos',
                status = 400,
                error = 'Invalid Parameters'
            )
        
        if request.method == 'GET':

            datos = CultivoService.obtener_horas_frio_variedad(
                nombre_variedad = nombre
            )

            if not datos:
                raise APIException(
                    message = f'No se han encontrado datos hora_frio para la variedad {nombre}',
                    status = 404,
                    error = 'Data Not Found'
                )
            
            return dataclass_to_json(datos)
        
        elif request.method == 'PATCH':

            horas_frio_max = request.args.get('frio_max')
            horas_frio_min = request.args.get('frio_min')

            if not (horas_frio_max or horas_frio_min):
                raise APIException(
                    message = f'No se puede actualizar las horas frio de la variedad {nombre} porque no se han definido sus nuevos valores (frio_max, frio_min)',
                    status = 400,
                    error = 'Invalid Parameters'
                )
            
            CultivoService.actualizar_horas_frio_variedad(
                nombre_variedad = nombre, 
                hora_frio_min = horas_frio_min,
                hora_frio_max = horas_frio_max
            )
            
            return jsonify(
                {
                    'success': 'true',
                    'message': f'Variedad {nombre} actualizada correctamente sus horas de frio'
                }
            )
    
    except APIException as e:
        logger.info(f"API Exception : {e}")
        return jsonify(
            {
                'success' : 'false',
                'code' : '500',
                'message' : 'Internal Error',
                'error' : str(e)
            }
        ), 500
    
@cultivo_bp.route('/crop/modelos/<string:codigo>/variedades', methods = ['GET'])
@log('../logs/fichero_salida.json')
def variedades_por_modelo(
    codigo : str
):
    try:
        if not codigo:
            raise APIException(
                message = 'Parametros de entrada incompletos',
                status = 400,
                error = 'Invalid Parameters'
            )
        
        datos = CultivoService.obtener_variedades_modelo(
            codigo_modelo = codigo
        )

        if not datos:
            raise APIException(
                message = f'No se han encontrado variedades que implementen el modelo {codigo}',
                status = 404,
                error = 'Data Not Found'
            )
        
        return dataclass_to_json(datos)
    
    except APIException as e:
        logger.info(f"API Exception : {e}")
        return jsonify(
            {
                'success' : 'false',
                'code' : '500',
                'message' : 'Internal Error',
                'error' : str(e)
            }
        ), 500

@cultivo_bp.route('/crop/<string:campo>', methods = ['GET', 'POST'])
@log('../logs/fichero_salida.json')
def obtener_crear_campos(
    campo : str
):
    RECURSOS = {
        "variedades": {
            "get_method": "obtener_variedades_disponibles",
            "post_method": "registrar_variedad_nueva",
            "filter_param": "cultivo",  # Parámetro opcional de filtro en GET
            "nombre_display": "variedad"
        },
        "modelos": {
            "get_method": "obtener_modelos_disponibles",
            "post_method": "registrar_modelo",
            "filter_param": None,
            "nombre_display": "modelo"
        },
        "etapas_fenologicas": {
            "get_method": "obtener_etapas_fenologicas",
            "post_method": None,
            "filter_param": None,
            "nombre_display": None
        },
        "cultivos": {
            "get_method": "obtener_cultivos_disponibles",
            "post_method": "registrar_cultivo_nuevo",
            "filter_param": None,
            "nombre_display": "cultivo"
        }
    }

    try:

        if not campo:
            raise APIException(
                message = 'Parametros invalidos, se debe especificar el campo',
                status = 400,
                error = 'Invalid Parameters'
            )

        if campo not in RECURSOS:
            raise APIException(
                message = f'Campo "{campo}" no soportado. Opciones: {", ".join(RECURSOS.keys())}',
                status = 400,
                error = 'Invalid Parameters'
            )
        
        config = RECURSOS[campo]
        
        if request.method == 'GET':
            # Obtener parámetro de filtro si existe
            filter_value = None
            if config["filter_param"]:
                filter_value = request.args.get(config["filter_param"])
            
            # Llamar al método del servicio dinámicamente
            get_method = getattr(CultivoService, config["get_method"])
            
            if filter_value:
                datos = get_method(**{config["filter_param"]: filter_value})
                print(datos)
            else:
                datos = get_method()
            
            logger.info(f"Datos recibidos: {datos}")
            
            if not datos:
                raise APIException(
                    message=f"No se encontraron datos de {config['nombre_display']}",
                    status=404,
                    error='Data Not Found'
                )
            
            return dataclass_to_json(datos)
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data:
                raise APIException(
                    message='Datos en JSON requeridos',
                    status=400,
                    error='Bad Request'
                )
            
            # Llamar al método del servicio dinámicamente
            if config['post_method']:
                post_method = getattr(CultivoService, config["post_method"])
                post_method(args=data)
                
                return jsonify(
                    {
                        'success': True,
                        'message': f'Se ha creado correctamente {config["nombre_display"]}',
                        'status': 201
                    }
                ), 201
            else:
                return jsonify(
                    {
                        'success': False,
                        'message': f'No se pueden agregar datos de tipo {campo}',
                        'status': '404' 
                    }
                )
    
    except APIException as e:
        logger.error(f"API Exception: {e}")
        return jsonify({
            'success': False,
            'status': e.status,
            'message': e.message,
            'error': e.error
        }), e.status
    
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({
            'success': False,
            'status': 500,
            'message': 'Internal Server Error',
            'error': str(e)
        }), 500

