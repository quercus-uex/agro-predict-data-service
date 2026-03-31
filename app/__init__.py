# Métodos para crear e inicializar la app y los distintos componentes y extensiones
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from config.config import Config
from .extensions import init_extensions
from flask_cors import CORS
from helpers.ApiExceptions import APIException
import os

load_dotenv()

def create_app(config_class = Config):
    app = Flask(__name__)

    # Evito problemas de CORS
    CORS(app, resources = {r"/*" : {"origins" : "*"}}) # Permite CORS para todas las rutas y origenes

    # Configuracion de la app
    app.config.from_object(config_class)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializo la db
    init_extensions(app = app)

    # Importación de modelos explicitamente, así el db_create_all() conoce la estructura del modelo
    with app.app_context():
        from . import models

    from .plagas import calendario_bp
    from .historicos import historic_bp
    from .forecast import forecast_bp
    from .cultivos import cultivo_bp
    from .sensores import sensores_bp
    from .metadata import metadata_bp

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

    return app

