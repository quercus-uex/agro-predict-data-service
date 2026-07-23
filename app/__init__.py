# Métodos para crear e inicializar la app y los distintos componentes y extensiones
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from config.config import Config
from .extensions import init_extensions
from flask_cors import CORS
from helpers.ApiExceptions import APIException
import os
import logging

logger = logging.getLogger(__name__)

load_dotenv()

def create_app(config_class = Config):
    app = Flask(__name__)

    if hasattr(config_class, 'validate_environment'):
        config_class.validate_environment()

    # Evito problemas de CORS
    CORS(app, resources = {r"/*" : {"origins" : "*"}}) # Permite CORS para todas las rutas y origenes

    # Configuracion de la app
    app.config.from_object(config_class)

    # Inicializo la db
    init_extensions(app = app)

    # Importación de modelos explicitamente, así el db_create_all() conoce la estructura del modelo
    with app.app_context():
        from . import models

    from app.plagas.routes import calendario_bp
    from app.historicos.routes import historic_bp
    from app.forecast.routes import forecast_bp
    from app.cultivos.routes import cultivo_bp
    from app.sensores.routes import sensores_bp
    from app.metadata.routes import metadata_bp

    app.register_blueprint(calendario_bp)
    app.register_blueprint(historic_bp)
    app.register_blueprint(forecast_bp)
    app.register_blueprint(cultivo_bp)
    app.register_blueprint(sensores_bp)
    app.register_blueprint(metadata_bp)

    @app.errorhandler(APIException)
    def handle_api_exception(e):
        return jsonify({
            'status' : e.status,
            'error' : e.error,
            'message' : e.message,
        }), e.status
    
    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logger.exception("Unhandled exception")

        return jsonify({
            'success': False,
            'status': 500,
            'message': 'Internal Server Error'
        }), 500

    return app

