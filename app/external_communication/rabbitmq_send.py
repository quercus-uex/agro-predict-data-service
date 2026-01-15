from rabbitmq_amqp_python_client import (
    Message, 
    OutcomeState, 
    Connection, 
    Environment
)
from typing import List


class RabbitMQPublisher():
    def create_publish(
        obj : tuple[Connection, Environment, List[str]], 
        texto : str
    ):
        # Creación del publisher
        publisher = obj[0].publisher(obj[2][0])

        # Creamos el mensaje que vamos a enviar por la cola
        bytes_texto = texto.encode("utf-8") # Los mensajes solo se pueden mandar por la cola con tipo bytes
        message = Message(body = bytes_texto)

        # Enviamos el mensaje y comprobamos su estado
        status = publisher.publish(message)

        # Control del estado del mensaje en la cola del broker
        match status.remote_state:
            case OutcomeState.ACCEPTED:
                print("Mensaje aceptado")
            case OutcomeState.REJECTED:
                print("Mensaje rechazado")
            case OutcomeState.RELEASED:
                print("Mensaje enviado")
        
        # Liberacion de memoria, cerrando el publisher
        publisher.close()