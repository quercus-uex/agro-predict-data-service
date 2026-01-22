# Inicialización del BluePrint FORECAST
from flask import Blueprint

forecast_bp = Blueprint('forecast', __name__, template_folder = 'templates')

from . import routes