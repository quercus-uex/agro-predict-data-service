"""
Extensiones de Flask
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_extensions(app):
    """Inicializo las extensiones con la aplicación Flask"""
    db.init_app(app)