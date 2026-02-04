# rabbitmq_config_pika.py
import pika
from config.config import Config

class RabbitMQConfig:
    @staticmethod
    def init_config():
        """
        Inicializa la conexión y devuelve:
        - connection: pika.BlockingConnection
        - channel: pika.Channel
        - queues: dict con las colas
        """
        params = pika.URLParameters(Config.RABBITMQ_CONNECTION)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Declaro las colas para asegurar que existen
        queue_raw = Config.QUEUE_IN_NAME
        queue_processed = Config.QUEUE_OUT_NAME

        channel.queue_declare(queue=queue_raw, durable=True)
        channel.queue_declare(queue=queue_processed, durable=True)

        queues = {
            "raw": queue_raw,
            "processed": queue_processed
        }

        return connection, channel, queues
