from rabbitmq_amqp_python_client import (
    Event,
    AMQPMessagingHandler,
    Connection,
    Environment
)
from typing import List

# Clase encargada de manejar los mensajes
class MessageHandler(AMQPMessagingHandler):
    def __init__(self):
        super().__init__()
        self._count = 0

    def on_message(self, event : Event):
        # Almacenamos el contenido del cuerpo del mensaje que está en la cola
        body = event.message.body

        print(f"Mensaje recibido: {body}")
        
        # Guardo el mensaje para reotornarlo luego
        self.last_message = body

        # Acepto el mensaje recibido para eliminarlo de la cola
        self.delivery_context.accept(event)

class RabbitMQConsumer():
    def receive_content(
        obj : tuple[Connection, Environment, List[str]]
    ):
        handler = MessageHandler()
        # Creo el consumidor del evento con la clase de manejador de mensajes
        consumer = obj[0].consumer(destination = obj[2][1], message_handler = handler)

        # Inicio el consumidor
        consumer.run(limit = 1) # Procesa solo un mensaje y termina

        return handler.last_message