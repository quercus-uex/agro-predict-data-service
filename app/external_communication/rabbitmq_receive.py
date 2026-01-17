from rabbitmq_amqp_python_client import (
    Event,
    AMQPMessagingHandler,
    Connection,
    Environment
)
from typing import List
import pickle

# Clase encargada de manejar los mensajes
class MessageHandler(AMQPMessagingHandler):
    def __init__(self):
        super().__init__()
        self._count = 0
        self.consumer = None # Referencia al consumidor para que el handler pueda pararlo

    def set_consmer(self, consumer):
        self.consumer = consumer

    def bytes_2_text(self, body):
        if isinstance(body, memoryview):
            return pickle.loads(body) # Deserializo el objeto de bytes que serializé con pickle al enviarlo
        if isinstance(body, (bytes, bytearray)):
            return body.decode("utf-8")
        
        return str(body)

    def on_message(self, event : Event):
        # Almacenamos el contenido del cuerpo del mensaje que está en la cola
        body_undecoded = event.message.body
               
        # Guardo el mensaje para reotornarlo luego
        self.last_message = self.bytes_2_text(body_undecoded)

        # Acepto el mensaje recibido para eliminarlo de la cola
        self.delivery_context.accept(event)

        # Para de esperar más mensajes una vez ya se ha leido un evento
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
        handler.set_consmer(consumer = consumer)
        
        # Inicio el consumidor
        consumer.run()

        return str(handler.last_message)