from rabbitmq_amqp_python_client import (
    Environment,
    AddressHelper
)
from config.config import Config
from typing import List

class RabbitMQConfig:
    def init_config():
        
        colas_dispoinibles = []

        # Creo conexion con RabbitMQ
        environment = Environment(uri=f"{Config.RABBITMQ_CONNECTION}")
        connection = environment.connection() # Crea y retorna una nueva conexion
        connection.dial() # Establece la conexion con el servidor AMQP

        # Creación de la referencia a la cola del broker de entrada
        queue_in_name = Config.QUEUE_IN_NAME # Nombre de la cola de entrada
        addr1 = AddressHelper.queue_address(queue_in_name)

        # Creación de la referencia a la cola del broker de salida
        queue_out_name = Config.QUEUE_OUT_NAME # Nombre de la cola de salida
        addr2 = AddressHelper.queue_address(queue_out_name)

        colas_dispoinibles.append(addr1)
        colas_dispoinibles.append(addr2)

        return connection, environment, colas_dispoinibles