"""
Extensiones de Flask
"""
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
from flask import jsonify
import yaml
import pathlib
import os

db = SQLAlchemy()

def init_extensions(app):
    """Inicializo las extensiones con la aplicación Flask"""
    db.init_app(app)
    register_swagger(app)

def register_swagger(app):
    """
    Registra el blueprint de swagger junto con su configuración para poder usarlo
    """
    swagger_ui_blueprint = get_swaggerui_blueprint(
        app.config['SWAGGER_URL'],
        app.config['API_URL'],
        config = {
            'app_name' : app.config['SERVICE_NAME'],
            'docExpansion' : 'none'
        } 
    )

    app.register_blueprint(
        swagger_ui_blueprint, 
        url_prefix = app.config['SWAGGER_URL']
    )

    @app.route(app.config['API_URL'])
    def serve_swagger_json():
        try:
            swagger_path = pathlib.Path(__file__).parent.parent / 'swagger/swagger.yml'
            print(f"Swagger path : {swagger_path}")
            with open(swagger_path, encoding = 'utf-8') as file:
                swagger_spec = yaml.safe_load(file)
                return jsonify(swagger_spec)
        except Exception as e:
            app.logger.error(f"Error cargando swagger.yml : {e}")
            return jsonify(
                {
                    "error" : "No se pudo cargar la especificación Swagger",
                    "details" : str(e)
                }
            ), 500