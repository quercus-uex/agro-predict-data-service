from flask import Blueprint

metadata_bp = Blueprint('metadata', __name__)

from . import routes