# Métodos para crear e inicializar la app y los distintos componentes y extensiones
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from config.config import Config
from .extensions import init_extensions, db
import os

load_dotenv()

def create_app(config_class = Config):
    app = Flask(__name__)

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

    app.register_blueprint(calendario_bp)
    app.register_blueprint(historic_bp)
    app.register_blueprint(forecast_bp)
    app.register_blueprint(cultivo_bp)

    return app

