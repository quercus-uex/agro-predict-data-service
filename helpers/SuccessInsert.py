
class SuccessInsert():
    """Respuesta exitosa para creación de objetos con la API"""
    def __init__(self, message, status=201):
        self.message = message
        self.status = status
