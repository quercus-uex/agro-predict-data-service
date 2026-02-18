from .cultivos_dto import (
    CultivoDTO,
    VariedadDTO,
    ModeloFrioDTO,
    EtapaFenologicaDTO,
    UmbralesTemperaturaDTO
)
from .cultivos_dao import CultivosDAO
from typing import Optional

class CultivoService:

    @staticmethod
    def _build_cultivos(
        datos
    ) -> Optional[CultivoDTO]:
        """
        Construye DTOs de cultivos en base a los datos proporcionados
        
        :param datos: Cultivos obtenidos de la base de datos
        :return: Optional[CultivoDTO]
        """
        if not datos:
            return None
        
        return CultivoDTO(
            nombre = datos.get('nombre'),
            nombre_cientifico = datos.get('nombre_cientifico'),
            descripcion = datos.get('descripcion')
        )

    @staticmethod
    def _build_variedades(
        datos
    ) -> Optional[VariedadDTO]:
        """
        Construy DTOs de variedades en base a los datos proporcionados

        :param datos: Variedades obtenidas de la base de datos
        :return: Optional[VariedadDTO]
        """
        if not datos:
            return None
        
        return VariedadDTO(
            nombre = datos.get('variedad_nombre'),
            horas_frio_min = datos.get('horas_frio_min'),
            horas_frio_max = datos.get('horas_frio_max'),
            modelo = ModeloFrioDTO(
                nombre = datos.get('modelo_nombre'),
                codigo = datos.get('codigo'),
                descripcion = datos.get('descripcion')
            )
        )
    
    @staticmethod
    def _build_etapa_fenologica(
        datos
    ) -> Optional[EtapaFenologicaDTO]:
        """
        Construye DTOs de etapas fenologicas en base a los datos obtenidos de la base de datos
        
        :param datos: Datos obtenidos de la base de datos
        :return: Etapa Fenologica pasada a DTO
        :rtype: EtapaFenologicaDTO
        """

        if not datos:
            return None
        
        return EtapaFenologicaDTO(
            nombre = datos.get('nombre'),
            codigo = datos.get('codigo'),
            orden = datos.get('orden')
        )
    
    @staticmethod
    def _build_umbrales(
        datos,
        nombre_variedad : str
    ) -> Optional[UmbralesTemperaturaDTO]:
        """
        Construye DTOs de umbrales de temperatura en base a los datos obtenidos
        
        :param datos: Datos obtenidos de temperatura
        :param nombre_variedad: Nombre de la variedad seleccionada
        :type nombre_variedad: str
        :return: DTO cargado de umbral de temperatura
        :rtype: UmbralesTemperaturaDTO | None
        """

        if not datos:
            return None
        
        return UmbralesTemperaturaDTO(
            nombre_variedad = nombre_variedad,
            etapa_fenologica = EtapaFenologicaDTO(
                nombre = datos.get('etapa_fenologica').get('nombre'),
                codigo = datos.get('etapa_fenologica').get('codigo'),
                orden = datos.get('etapa_fenologica').get('orden')
            ),
            critico = datos.get('critico'),
            alto = datos.get('alto'),
            moderado = datos.get('moderado'),
            bajo = datos.get('bajo')
        )
    
    @staticmethod
    def _build_modelos(
        datos
    ) -> Optional[ModeloFrioDTO]:
        """
        Construye DTOs de modelos de frio en base a los datos obtenidos
        
        :param datos: Datos obtenidos de la base de datos
        :return: DTO construido y cargado
        :rtype: ModeloFrioDTO | None
        """

        if not datos:
            return None

        return ModeloFrioDTO(
            nombre = datos.get('nombre'),
            codigo = datos.get('codigo'),
            descripcion = datos.get('descripcion')
        )

    @staticmethod
    def obtener_cultivos_disponibles() -> Optional[list[CultivoDTO]]:
        """
        Obtiene los cultivos disponibles, almacenados en la base de datos
        """

        datos = CultivosDAO.obtener_cultivos()

        if not datos:
            return None
        
        return [
            dto
            for cultivo in datos
            if (dto := CultivoService._build_cultivos(cultivo)) is not None
        ]

    #======== OBTENCIÓN DE DATOS ========#
    @staticmethod
    def obtener_variedades_disponibles(
        cultivo : Optional[str]
    ) -> Optional[list[VariedadDTO]]:        
        """
        Obtiene las variedades disponibles, si se especifica, las variedades de los cultivos
        """

        datos = CultivosDAO.obtener_variedades(
            cultivo = cultivo if cultivo else None
        )

        if not datos:
            return None
        
        return [
            dto
            for variedad in datos
            if (dto := CultivoService._build_variedades(variedad)) is not None
        ]
    
    @staticmethod
    def obtener_etapas_fenologicas() -> Optional[list[EtapaFenologicaDTO]]:
        """
        Obtiene las etapas fenologicas disponibles en la base de datos
        
        :return: Lista de EtapasFenologicasDTO
        :rtype: list[EtapaFenologicaDTO] | None
        """

        datos = CultivosDAO.obtener_etapas_fenologicas()

        if not datos:
            return None
        
        return [
            dto
            for etapa in datos
            if (dto := CultivoService._build_etapa_fenologica(etapa)) is not None
        ]
    
    @staticmethod
    def obtener_modelos_disponibles() -> Optional[list[ModeloFrioDTO]]:
        """
        Obtiene los modelos de horas_frio disponibles
        
        :return: Lista de modelos disponibles
        :rtype: Optional[list[ModeloFrioDTO]]
        """

        datos = CultivosDAO.obtener_modelos_frio()

        if not datos:
            return None
        
        print(f"Datos : {datos}")
        
        return [
            dto
            for modelo in datos
            if (dto := CultivoService._build_modelos(modelo)) is not None
        ]
    
    @staticmethod
    def obtener_horas_frio_variedad(
        nombre_variedad : str
    ) -> dict:
        """
        Obtiene el umbral de horas frio sobre una variedad seleccionada
        
        :param nombre_variedad: Nombre de la variedad seleccionada
        :type nombre_variedad: str
        :return: Horas frio maximas y mínimas sobre la variedad seleccionada
        :rtype: dict
        """

        if not nombre_variedad:
            raise ValueError("Error, se debe especificar el nombre de la variedad")
        
        datos = CultivosDAO.obtener_horas_frio_variedad(
            nombre_variedad = nombre_variedad
        )

        if not datos:
            return None
        
        return {
            "nombre_variedad" : nombre_variedad,
            "horas_frio_max" : datos.get('horas_frio_max'),
            "horas_frio_min" : datos.get('horas_frio_min')
        }
    
    @staticmethod
    def obtener_umbrales_variedad(
        nombre_variedad : str
    ) -> Optional[list[UmbralesTemperaturaDTO]]:
        """
        Obtiene los umbrales de temperatura sobre una variedad seleccionada
        
        :param nombre_variedad: Nombre de la variedad seleccionada
        :type nombre_variedad: str
        :return: Lista de umbrales de temperatura para cada etapa fenologica de la variedad seleccionada
        :rtype: Optional[list[UmbralesTemperaturaDTO]]
        """

        if not nombre_variedad:
            raise ValueError("Error, se debe especificar el nombre de la variedad")
        
        datos = CultivosDAO.umbrales_por_variedad(
            nombre_variedad = nombre_variedad
        )

        if not datos:
            return None
        
        return [
            dto
            for umbral in datos
            if (dto := CultivoService._build_umbrales(umbral, nombre_variedad)) is not None
        ]

    @staticmethod
    def obtener_variedades_modelo(
        codigo_modelo : str
    ) -> Optional[list[VariedadDTO]]:
        """
        Obtener variedades que usan un modelo seleccionado
        
        :param codigo_umbral: Identificador público del modelo
        :type codigo_modelo: str
        :return: Lista de DTOs cargados
        :rtype: list[VariedadDTO] | None
        """

        if not codigo_modelo:
            raise ValueError("Error, se debe especificar el codigo del umbral")
        
        datos = CultivosDAO.obtener_variedades_por_modelo(
            nombre_modelo = codigo_modelo
        )

        if not datos:
            return None
        
        return [
            dto
            for variedad in datos
            if (dto := CultivoService._build_variedades(variedad)) is not None
        ]
    
    #======== INSERCION DE DATOS ========#
    @staticmethod
    def registrar_cultivo_nuevo(
        args : dict
    ):
        """
        Registra un nuevo cultivo en la base de datos
        
        :param args: Atributos del nuevo cultivo
        :type args: dict
        """
        if not args:
            raise ValueError("Error, se deben especificar datos para crear un cultivo")
        
        new_cultivo = CultivosDAO.crear_cultivo(
            nombre = args.get('nombre'),
            nombre_cientifico = args.get('nombre_cientifico'),
            descripcion = args.get('descripcion')
        )

        if not new_cultivo:
            raise ValueError(f"Error, no se ha podido crear el cultivo con los datos {args}")
        

    @staticmethod
    def registrar_variedad_nueva(
        args : dict
    ):
        """
        Registra una nueva variedad sobre el cultivo asociado en la base de datos
        
        :param args: Atributos de la nueva variedad
        :type args: dict
        """
        if not args:
            raise ValueError("Error, se deben especificar datos para crear la variedad")
        
        new_variedad = CultivosDAO.crear_variedad(
            nombre_variedad = args.get('nombre'),
            nombre_cultivo_asociado = args.get('cultivo'),
            horas_frio_min = args.get('horas_frio_min'),
            horas_frio_max = args.get('horas_frio_max'),
            nombre_modelo_horas_frio = args.get('modelo')
        )

        if not new_variedad:
            raise ValueError(f"Error, no se ha podido crear la variedad con los datos {args}")
        
    @staticmethod
    def registrar_umbral(
        nombre_variedad : str,
        args : dict
    ):
        """
        Registra un nuevo umbral de temperatura para una variedad seleccionada
        
        :param nombre_variedad: Nombre de la variedad que se decide crear el nuevo umbral
        :type nombre_variedad: str
        :param args: Atributos del nuevo umbral
        :type args: dict
        """
        if not nombre_variedad:
            raise ValueError("Error, se debe indicar la variedad asociada al umbral a crear")
        if not args:
            raise ValueError("Error, se deben especificar datos para crear el umbral")

        new_umbral = CultivosDAO.crear_umbrales_temperatura(
            nombre_variedad = nombre_variedad,
            nombre_etapa_fenologica = args.get('etapa'),
            umbrales_criticidad = {
                "critico" : args.get('critico'),
                "alto" : args.get('alto'),
                "moderado" : args.get('moderado'),
                "bajo" : args.get('bajo')
            }
        )

        if not new_umbral:
            raise ValueError(f"Error, no se ha podido crear un umbral {args} para la variedad {nombre_variedad}")

    @staticmethod
    def registrar_modelo(
        args : dict
    ):
        """
        Registra un nuevo modelo de horas-frio en la base de datos
        
        :param args: Atributos del nuevo modelo
        :type args: dict
        """
        if not args:
            raise ValueError("Error, se deben especificar datos para crear el modelo")
        
        new_modelo = CultivosDAO.crear_modelos_horas_frio(
            nombre = args.get('nombre'),
            codigo = args.get('codigo'),
            descripcion = args.get('descripcion')
        )

        if not new_modelo:
            raise ValueError(f"Error, no se ha podido crear el modelo {args}")
        
    #======== ACTUALIZACION DE DATOS ========#
    @staticmethod
    def actualizar_horas_frio_variedad(
        nombre_variedad : str,
        hora_frio_max : int,
        hora_frio_min : int
    ):
        """
        Actualiza las horas de frio sobre una variedad seleccionada
        
        :param nombre_variedad: Variedad a actualizar
        :type nombre_variedad: str
        :param hora_frio_max: Nuevo valor de horas_frio_max 
        :type hora_frio_max: int
        :param hora_frio_min: Nuevo valor de horas_frio_min
        :type hora_frio_min: int
        """

        if not all([nombre_variedad, hora_frio_max, hora_frio_min]):
            raise ValueError("Error, se deben especificar los parámetros indicados para actualizar")
        
        actualizacion = CultivosDAO.actualizar_rango_horas_frio(
            nombre_variedad = nombre_variedad,
            horas_max_frio = hora_frio_max,
            horas_min_frio = hora_frio_min
        )