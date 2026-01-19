# Inicialización del BluePrint ACTUALES
from flask import Blueprint

actuales_bp = Blueprint('actuales', __name__, template_folder = 'templates')

from . import routes