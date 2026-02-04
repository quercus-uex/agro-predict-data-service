# rabbitmq_receive_pika.py
import pika
import json

class RabbitMQConsumer:

    @staticmethod
    def receive_content(
        channel: pika.adapters.blocking_connection.BlockingChannel,
        queue_name: str):
        # Callback que se llama cuando llega un mensaje
        result = {}

        def callback(ch, method, properties, body):
            nonlocal result
            result = json.loads(body.decode('utf-8'))
            ch.basic_ack(delivery_tag=method.delivery_tag)
            # Paro el loop al recibir el primer mensaje
            channel.stop_consuming()

        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback
        )

        channel.start_consuming()
        return result
