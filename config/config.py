import os
from dotenv import load_dotenv
from circuitbreaker import CircuitBreaker
import requests

load_dotenv()

class Config:
    SIAR_SERVICE_DATA_URL = os.getenv('SIAR_SERVICE_DATA_URL')
    SIAR_SERVICE_INFO_URL = os.getenv('SIAR_SERVICE_INFO_URL')
    AEMET_SERVICE_CURRENT_URL = os.getenv('AEMET_SERVICE_CURRENT_URL')
    AEMET_SERVICE_FUTURE_URL = os.getenv('AEMET_SERVICE_FUTURE_URL')
    ITACYL_SERVICE_BASE_URL = os.getenv('ITACYL_SERVICE_BASE_URL')
    DTAGRO_SERVICE_BASE_URL = os.getenv('DTAGRO_SERVICE_BASE_URL')
    DTAGRO_API_TOKEN = os.getenv('DTAGRO_API_TOKEN')
    QUEUE_IN_NAME = os.getenv('QUEUE_IN_NAME')
    QUEUE_OUT_NAME = os.getenv('QUEUE_OUT_NAME')
    RABBITMQ_CONNECTION = os.getenv('RABBITMQ_CONNECTION')

class CircuitBreakerPersonalizado(CircuitBreaker):
    FAILURE_THRESHOLD = 7
    RECOVERY_TIMEOUT = 60
    EXPECTED_EXCEPTION = requests.exceptions.RequestException

class DevelopementConfig(Config):
    """DEVELOPEMENT CONFIG"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """TESTING CONFIG"""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

class ProductionConfig(Config):
    """PRODUCTION CONFIG"""
    DEGUB = False
    TESTING = False

# Config Mapping
config = {
    'development': DevelopementConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopementConfig
}