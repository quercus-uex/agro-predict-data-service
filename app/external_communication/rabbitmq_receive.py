from rabbitmq_amqp_python_client import (
    Event,
    AMQPMessagingHandler,
    Connection,
    Environment
)
from typing import List
import json

# Clase encargada de manejar los mensajes
class MessageHandler(AMQPMessagingHandler):
    def __init__(self):
        super().__init__()
        self._count = 0
        self.consumer = None # Referencia al consumidor para que el handler pueda pararlo
        self.last_message = None

    def set_consumer(self, consumer):
        self.consumer = consumer

    def bytes_2_text(self, body):
        if isinstance(body, memoryview):
            #return pickle.loads(body) # Deserializo el objeto de bytes que serializé con pickle al enviarlo
            body = bytes(body)
        if isinstance(body, (bytes, bytearray)):
            return body.decode("utf-8")
        
        return str(body)

    def on_message(self, event: Event):
        # memoryview -> bytes -> JSON
        body = event.message.body
        if isinstance(body, memoryview):
            body = bytes(body)
        self.last_message = json.loads(body.decode("utf-8"))

        # Aceptar el mensaje
        self.delivery_context.accept(event)

        # Detener el consumidor al leer un solo mensaje
        if self.consumer:
            self.consumer.stop()

class RabbitMQConsumer():
    def receive_content(
        obj : tuple[Connection, Environment, List[str]]
    ):
        handler = MessageHandler()

        # Creo el consumidor del evento con la clase de manejador de mensajes
        consumer = obj[0].consumer(destination = obj[2][1], message_handler = handler)

        # Construyo la referencia al consumidor
        handler.set_consumer(consumer = consumer)
        
        # Inicio el consumidor
        consumer.run()

        return handler.last_message
