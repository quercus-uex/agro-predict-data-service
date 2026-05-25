import pytest
from app import create_app
from app.extensions import db
from config.config import TestingConfig
import fakeredis

@pytest.fixture
def app():
    app = create_app(config_class = TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_redis(monkeypatch):
    # Simulo un servicio de redis en memoria
    fake_r = fakeredis.FakeStrictRedis(decode_response=True)
    monkeypatch.setattr('app.historicos.tasks.r', fake_r)
    return fake_r