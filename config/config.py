import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    pass

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