import logging
from clients.siar_client import SiARClient
from flask import app

logger = logging.getLogger(__name__)

siar_client = None
aemet_client = None
itacyl_client = None

def init_app(app):
    global siar_client, aemet_client, itacyl_client
    siar_client = SiARClient(app)
