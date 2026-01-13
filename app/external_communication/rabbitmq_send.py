from rabbitmq_amqp_python_client import Message, OutcomeState, Connection, Environment

class RabbitMQPublisher():
    def create_publish(obj : tuple[Connection, Environment], texto : str):
        # Creación del publisher
        publisher = obj[0].publisher(obj[2])

        # Creamos el mensaje que vamos a enviar por la cola
        message = Message(body = texto)

        # Enviamos el mensaje y comprobamos su estado
        status = publisher.publish(message)

        match status.remote_state:
            case OutcomeState.ACCEPTED:
                print("Mensaje aceptado")
            case OutcomeState.REJECTED:
                print("Mensaje rechazado")
            case OutcomeState.RELEASED:
                print("Mensaje enviado")
        
        # Liberacion de memoria
        publisher.close()
        obj[0].close()
        obj[1].close()