# rabbitmq_send_pika.py
import pika

class RabbitMQPublisher:
    
    @staticmethod
    def create_publish(
        channel: pika.adapters.blocking_connection.BlockingChannel,
        queue_name: str,
        texto: str
    ):
        # Publico el mensaje str en UTF-8
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=texto.encode('utf-8'),
            properties=pika.BasicProperties(
                delivery_mode=2  # Mensaje persistente
            )
        )
        print(f"Mensaje enviado a la cola '{queue_name}'")
