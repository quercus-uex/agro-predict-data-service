from . import cultivo_bp
from ..decorator.log_decorator import log
from ..globals.dto2dict import dataclass_to_json
from helpers.ApiExceptions import APIException
from .services.cultivos_service import CultivoService
from .services.cultivo_plaga_service import CultivoPlagaService
from .services.cultivo_parcela_service import CultivoParcelaService
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)


@cultivo_bp.route('/crop/variedades/<string:nombre>/umbrales', methods = ['GET', 'POST'])
@log('../logs/fichero_salida.json')
def umbrales_variedad(
    nombre : str
):
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
        
    
    

@cultivo_bp.route('/crop/variedades/<string:nombre>/horas_frio', methods = ['GET', 'PATCH'])
@log('../logs/fichero_salida.json')
def horas_frio_variedad(
    nombre : str
):
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
    
    
@cultivo_bp.route('/crop/modelos/<string:codigo>/variedades', methods = ['GET'])
@log('../logs/fichero_salida.json')
def variedades_por_modelo(
    codigo : str
):
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
    

@cultivo_bp.route('/crop/plague', methods = ['GET'])
@log('../logs/fichero_salida.json')
def obtener_cultivos_asociados_plagas():
    
    nombre_cultivos = request.args.get('cultivos')

    if not nombre_cultivos:
        raise APIException(
            status = 400, 
            message = 'Se debe indicar el valor de un query param : cultivos',
            error = 'Invalid Parameters'
        )
    
    nombre_cultivos_lista = [c.strip() for c in nombre_cultivos.split(',')]

    datos_cultivo_plaga = CultivoPlagaService.obtener_cultivo_plaga_asociado(
        nombres_cultivo = nombre_cultivos_lista
    )

    if not datos_cultivo_plaga:
        raise APIException(
            status = 400,
            message = f'No se han encontrado datos de plagas asociado a los cultivos {nombre_cultivos}',
            error = 'Data Not Found'
        )
    
    return dataclass_to_json(datos_cultivo_plaga)
    
@cultivo_bp.route('/crop/parcel', methods = ['GET'])
@log('../logs/fichero_salida.json')
def obtener_cultivos_asociados_a_parcelas():
    parcela_id = request.args.get('parcela')
    nombre_cultivo = request.args.get('cultivo')

    if not parcela_id and not nombre_cultivo:
        raise APIException(
            status = 400,
            message = 'Se debe especificar el nombre de la parcela junto con el del cultivo para ver si comprobar la asociación',
            error = 'Invalid Parameters'
        )
    
    datos = CultivoParcelaService.obtener_asociacion_parcela_cultivo(
        nombre_cultivo = nombre_cultivo,
        parcela_id = parcela_id
    )
    
    if not datos:
        raise APIException(
            status = 404,
            message = f'No se registran datos de la asociación entre {nombre_cultivo} - {parcela_id} por el sistema',
            error = 'Data Not Found'
        )
    
    return dataclass_to_json(datos)
    

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