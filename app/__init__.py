# Métodos para crear e inicializar la app y los distintos componentes y extensiones
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://mendo:12345@localhost:3307/tfg'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Registro de los Blueprints
    from .actuales import actuales_bp
    app.register_blueprint(actuales_bp)

    from .calendario import calendario_bp
    app.register_blueprint(calendario_bp)

    from .catalogo import catalogo_bp
    app.register_blueprint(catalogo_bp)

    from .historicos import historic_bp
    app.register_blueprint(historic_bp)

    from .pronostico import pronostico_bp
    app.register_blueprint(pronostico_bp)

    return app

