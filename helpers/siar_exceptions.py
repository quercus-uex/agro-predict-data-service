from .ApiExceptions import APIException

class SiARFechaInvalidaError(APIException):
    """
    La fecha inicial es inferior a la mínima autorizada por SiAR
    """
    pass

class SiARLimiteDiarioError(APIException):
    """
    Se ha alcanzado el limite diario de peticiones a realizar
    """
    pass

class SiARAutenticarError(APIException):
    """
    Se obtiene al producirse un error de autenticación con el servicio SiAR
    """
    pass