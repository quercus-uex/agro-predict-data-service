from rabbitmq_amqp_python_client import (
    Environment,
    AddressHelper
)
from config.config import Config

class RabbitMQConfig:
    def init_config():
        # Nombre de la cola a crear
        queue_name = Config.QUEUE_NAME

        # Creo conexion con RabbitMQ
        environment = Environment(uri=f"{Config.RABBITMQ_CONNECTION}")
        connection = environment.connection() # Crea y retorna una nueva conexion
        connection.dial() # Establece la conexion con el servidor AMQP

        # Creación de la cola
        addr = AddressHelper.queue_address(queue_name)

        return connection, environment, addr