from flask import Blueprint

cultivo_bp = Blueprint('cultivos', __name__, template_folder = 'templates')

from . import routes