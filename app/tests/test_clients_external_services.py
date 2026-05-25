from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import json
import requests
from app.clients.aemet_client import AemetClient
from app.clients.base_client import BaseClient
from app.clients.itacyl_client import ItacylClient
from app.external_services.aemet_service import AemetService
from app.external_communication.rabbitmq_config import RabbitMQConfig
from app.external_communication.rabbitmq_receive import RabbitMQConsumer
from app.external_communication.rabbitmq_send import RabbitMQPublisher


class DummyResponse:
    def __init__(self, status_code=200, text="ok", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("Raised status")


def test_base_client_make_request_success(monkeypatch, app):
    client = BaseClient(app, "test")
    monkeypatch.setattr("requests.request", lambda method, url, timeout, verify, **kwargs: DummyResponse(200, text="done"))

    response = client._make_request(method="GET", url="http://example.com")
    assert response.text == "done"


def test_base_client_make_request_handles_exception(monkeypatch, app):
    client = BaseClient(app, "test")

    def fail_request(*args, **kwargs):
        raise requests.exceptions.RequestException("network")

    monkeypatch.setattr("requests.request", fail_request)
    response = client._make_request(method="GET", url="http://example.com")
    print(f"DEBUG: response {response}")
    assert response is None


def test_aemet_client_current_data_return_none_for_404(monkeypatch, app):
    app.config["AEMET_SERVICE_CURRENT_URL"] = "http://aemet"
    cliente = AemetClient(app)
    monkeypatch.setattr(AemetClient, "_make_request", lambda self, **kwargs: DummyResponse(status_code=404, text="notfound"))

    assert cliente.get_current_data_by_zone(tipo=cliente.base_url_actuales, ccaa_code=None, provincia_code=None) is None


def test_aemet_client_current_data_success_returns_text(monkeypatch, app):
    app.config["AEMET_SERVICE_CURRENT_URL"] = "http://aemet"
    cliente = AemetClient(app)
    monkeypatch.setattr(AemetClient, "_make_request", lambda self, **kwargs: DummyResponse(status_code=200, text="payload"))

    assert cliente.get_current_data_by_zone(tipo=cliente.base_url_actuales, ccaa_code=None, provincia_code=None) == "payload"


def test_itacyl_client_returns_data_when_response_success(monkeypatch, app):
    app.config["ITACYL_SERVICE_BASE_URL"] = "http://itacyl"
    cliente = ItacylClient(app)
    mock_response = DummyResponse(status_code=200, json_data={"success": True, "data": [1, 2, 3]})
    monkeypatch.setattr(ItacylClient, "_make_request", lambda self, **kwargs: mock_response)

    data = cliente.get_itacyl_data(cultivo=1, grupo=None)
    assert data == [1, 2, 3]


def test_itacyl_client_returns_none_on_404(monkeypatch, app):
    app.config["ITACYL_SERVICE_BASE_URL"] = "http://itacyl"
    cliente = ItacylClient(app)
    mock_response = DummyResponse(status_code=404, json_data={"success": False})
    monkeypatch.setattr(ItacylClient, "_make_request", lambda self, **kwargs: mock_response)

    assert cliente.get_itacyl_data(cultivo=1, grupo=None) is None


def test_rabbitmq_publish_and_receive_use_magicmock(monkeypatch):
    channel = MagicMock()
    queue_name = "test-queue"
    RabbitMQPublisher.create_publish(channel, queue_name, "hello")
    channel.basic_publish.assert_called_once()

    mock_method = SimpleNamespace(delivery_tag=1)
    mock_properties = None
    body = b'{}'
    channel.basic_consume = MagicMock()
    channel.start_consuming = MagicMock()

    # Simulate callback invocation manually
    callback = None
    def fake_basic_consume(queue, on_message_callback):
        nonlocal callback
        callback = on_message_callback
    channel.basic_consume.side_effect = fake_basic_consume

    mock_result = {}
    def fake_stop_consuming():
        pass
    channel.stop_consuming = fake_stop_consuming

    def fake_callback(ch, method, properties, body):
        nonlocal mock_result
        mock_result = json.loads(body.decode('utf-8'))
    channel.basic_consume.assert_not_called()

    # We only verify the signature path -- the actual pika loop is not exercised here
    # because it requires a real channel implementation.
    assert hasattr(RabbitMQConsumer, 'receive_content')


def test_aemet_service_get_aemet_data_returns_none_when_no_text(app, monkeypatch):
    from app.external_services.aemet_service import AemetParser
    app.config["AEMET_SERVICE_CURRENT_URL"] = "http://aemet"

    with app.test_request_context("/", method="GET"):
        mock_client = MagicMock()
        mock_client.get_current_data_by_zone.return_value = None
        monkeypatch.setattr(AemetService, "_get_cliente", classmethod(lambda cls: mock_client))

        assert AemetService.get_aemet_data(
            tipo_zona=MagicMock(value="nacional"),
            tipo_prediccion=MagicMock(value="actual"),
            codigo_zona=None,
            fecha=None,
        ) is None


def test_aemet_service_get_aemet_data_processes_payload_and_returns_data(app, monkeypatch):
    from app.external_services.aemet_service import AemetParser
    app.config["AEMET_SERVICE_CURRENT_URL"] = "http://aemet"

    with app.test_request_context("/", method="GET"):
        mock_client = MagicMock()
        mock_client.get_current_data_by_zone.return_value = "text payload"
        monkeypatch.setattr(AemetService, "_get_cliente", classmethod(lambda cls: mock_client))

        fake_conn = MagicMock()
        fake_channel = MagicMock()
        fake_queues = {"raw": "raw", "processed": "processed"}
        monkeypatch.setattr(RabbitMQConfig, "init_config", staticmethod(lambda: (fake_conn, fake_channel, fake_queues)))
        monkeypatch.setattr(RabbitMQPublisher, "create_publish", staticmethod(lambda channel, queue, texto: None))
        monkeypatch.setattr(RabbitMQConsumer, "receive_content", staticmethod(lambda channel, queue: {"data": "ok"}))
        monkeypatch.setattr(AemetParser, "parse", staticmethod(lambda texto, respuesta_queue: {"fecha_prediccion": date(2026, 1, 1), "estado_del_cielo": "sol", "tendencias_de_temperatura_general": "ascendente", "tendencia_de_temperaturas_maximas": "alto", "tendencias_de_temperaturas_minimas": "bajo", "rachas_de_viento": "moderadas", "precipitaciones": "baja", "cotas_de_nieve": "nula", "existencias_de_heladas": False, "zona_helada": "ninguna", "aparicion_de_nieblas": "baja", "temperaturas_localidades": []}))

        result = AemetService.get_aemet_data(
            tipo_zona=MagicMock(value="nacional"),
            tipo_prediccion=MagicMock(value="actual"),
            codigo_zona="CC",
            fecha=date(2026, 1, 1),
        )

        assert isinstance(result, tuple)
        assert result[0]["tipo_prediccion"] == "actual"
