# Inicialización del BluePrint HISTORICO
from flask import Blueprint

historic_bp = Blueprint('historico', __name__, template_folder = 'templates')

from . import routes