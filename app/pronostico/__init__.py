# Inicialización del BluePrint PRONOSTICO
from flask import Blueprint

pronostico_bp = Blueprint('pronostico', __name__, template_folder = 'templates')

from . import routes