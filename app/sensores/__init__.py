from flask import Blueprint

sensores_bp = Blueprint('sensores', __name__)

from . import routes