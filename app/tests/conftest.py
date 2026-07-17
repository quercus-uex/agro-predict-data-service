import os
import pytest
from app import create_app
from app.extensions import db
from config.config import TestingConfig
import fakeredis

@pytest.fixture(scope="session", autouse=True)
def reset_log_file():
    """Recrea app/logs/fichero_salida.json antes de la suite para que exista
    (el .gitignore no lo trackea) y quede vacío, con solo lo generado en esta ejecución."""
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    if (os.path.exists(log_dir) and not os.path.isdir(log_dir)):
        os.remove(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "fichero_salida.json")
    open(log_path, "w", encoding="utf-8").close()
    yield

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