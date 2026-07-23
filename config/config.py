import os
from dotenv import load_dotenv
from circuitbreaker import CircuitBreaker
from pathlib import Path
import requests
from kombu import Queue

load_dotenv()

class Config:
    REQUIRED_ENV_VARS = (
        'SQLALCHEMY_DATABASE_URL',
        'SIAR_SERVICE_DATA_URL',
        'SIAR_SERVICE_INFO_URL',
        'AEMET_SERVICE_CURRENT_URL',
        'AEMET_SERVICE_FUTURE_URL',
        'ITACYL_SERVICE_BASE_URL',
        'DTAGRO_SERVICE_BASE_URL',
        'DTAGRO_API_TOKEN',
        'QUEUE_IN_NAME',
        'QUEUE_OUT_NAME',
        'RABBITMQ_CONNECTION',
        'REDIS_URL',
    )

    OPTIONAL_ENV_VARS = (
        'REDIS_HOST',
        'REDIS_PORT',
        'REDIS_DB',
        'REDIS_USER',
        'REDIS_PASS',
        'TEST_DATABASE_URL',
    )

    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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

    # Swagger
    SWAGGER_URL = '/api/v1/ui'
    API_URL = '/api/v1/swagger.json'

    # Aplicacion
    SERVICE_NAME = "Servicio de datos"
    SERVICE_VERSION = "1.0.0"

    # CELERY
    CELERY = {
        "broker_url"    : os.getenv("RABBITMQ_CONNECTION"),
        "result_backend": os.getenv("REDIS_URL"),
        "worker_pool"   : "solo" if os.name == "nt" else "prefork",
        "worker_disable_mingle" : True,
        "task_create_missing_queues" : False,
        "task_default_queue" : "default",
        "task_queues" : (Queue("default", durable = True),),
        "redis_backend_use_ssl": False,
        "redis_username": os.getenv("REDIS_USER"),
        "redis_password": os.getenv("REDIS_PASS"),  # ← extrae el password aparte
        "redis_host"    : os.getenv("REDIS_HOST", "localhost"),
        "redis_port"    : int(os.getenv("REDIS_PORT", 6379)),
        "redis_db"      : int(os.getenv("REDIS_DB", 0)),
    }

    # Metadata
    @staticmethod
    def obtener_ruta_contenido_metadatos(tipo : str):
        return Path(__file__).parent.parent / f"app/data/{tipo}"

    @classmethod
    def validate_environment(cls):
        missing_vars = []
        empty_vars = []

        for var_name in cls.REQUIRED_ENV_VARS:
            value = os.getenv(var_name)
            if value is None:
                missing_vars.append(var_name)
            elif isinstance(value, str) and not value.strip():
                empty_vars.append(var_name)

        if missing_vars or empty_vars:
            parts = []
            if missing_vars:
                parts.append(f"faltan: {', '.join(sorted(missing_vars))}")
            if empty_vars:
                parts.append(f"vacias: {', '.join(sorted(empty_vars))}")
            detail = ' | '.join(parts)
            raise RuntimeError(
                f"Variables de entorno invalidas ({detail}). Revisa el archivo .env o las variables del contenedor."
            )

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
    REQUIRED_ENV_VARS = ()
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

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