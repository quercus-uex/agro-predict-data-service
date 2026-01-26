# Métodos para crear e inicializar la app y los distintos componentes y extensiones
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from config.config import Config
import os

load_dotenv()
db = SQLAlchemy()

def create_app(config_class = Config):
    app = Flask(__name__)

    app.config.from_object(config_class)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Importación de modelos explicitamente, así el db_create_all() conoce la estructura del modelo
    with app.app_context():
        from . import models

    from .plagas import calendario_bp
    app.register_blueprint(calendario_bp)

    from .catalogo import catalogo_bp
    app.register_blueprint(catalogo_bp)

    from .historicos import historic_bp
    app.register_blueprint(historic_bp)

    from .forecast import forecast_bp
    app.register_blueprint(forecast_bp)

    return app

