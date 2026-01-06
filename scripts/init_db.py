from flask import app
from app import db

# Inicialización de la estructura de la base de datos
with app.app_context():
        db.create_all()
        print("Base de datos inicializada")