from .historico_dao import HistoricDAO
from datetime import datetime
from ..models import IngestaStatus
from .historico_dto import *
from ..ingesta.ingesta_dto import ProcesoIngestaDTO
from ..ingesta.ingesta_dao import IngestaDAO
from ..ingesta.ingesta_service import IngestionService
from ..ingesta.ingesta_thread import lanzar_ingesta_background
from datetime import timedelta
import logging
import time

logger = logging.getLogger(__name__)

# Mapa tipo → (método DAO, builder de DTO, clave de valores en el dict)
_TIPO_CONFIG: dict[TipoHistorico, tuple] = {
    TipoHistorico.HORA:   (HistoricDAO.define_computing_data_hora,   "_build_historico_hora",   "valores_horarios"),
    TipoHistorico.DIA:    (HistoricDAO.define_computing_data_dia,    "_build_historico_dia",    "valores_diarios"),
    TipoHistorico.SEMANA: (HistoricDAO.define_computing_data_semana, "_build_historico_semana", "valores_semanales"),
}


class HistoricService:

    # -------------------------------------------------------------------------
    # Helpers privados de DTO
    # -------------------------------------------------------------------------

    @staticmethod
    def _horas_pico(horas_pico: dict, key: str):
        """Devuelve el valor de horas_pico solo si existe, evitando el patrón 'x if x else None'."""
        return horas_pico.get(key) or None

    @staticmethod
    def _estaciones_usadas(data: dict, estacion_id) -> list | None:
        """Devuelve las estaciones usadas solo cuando la consulta es a nivel provincial."""
        return data.get("estaciones_usadas") if estacion_id is None else None

    # -------------------------------------------------------------------------
    # Builders de DTO
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_historico_hora(data: dict, estacion_id) -> list:
        """Construye DTOs horarios."""
        return [
            HistHorasDTO(
                horaMin      = v.get("hora"),
                tempMedia    = v.get("temp_media"),
                humedadMedia = v.get("humedad_media"),
                velViento    = v.get("vel_viento"),
                precipitacion = v.get("precipitacion"),
                estacion     = v.get("estacion"),
                radiacion    = v.get("radiacion"),
                estaciones   = HistoricService._estaciones_usadas(data, estacion_id),
                provincia    = v.get("provincia"),
                fecha        = v.get("fecha")
            )
            for v in data.get("valores_horarios", [])
        ]

    @staticmethod
    def _build_historico_dia(data: dict, estacion_id) -> list:
        """Construye DTOs diarios."""
        horas_pico = data.get("horas_pico", {})
        return [
            HistDiasDTO(
                tempMedia     = v.get("temp_media"),
                tempMax       = v.get("temp_max"),
                horMinTempMax = HistoricService._horas_pico(horas_pico, "hora_temp_max"),
                tempMin       = v.get("temp_min"),
                horMinTempMin = HistoricService._horas_pico(horas_pico, "hora_temp_min"),
                humedadMedia  = v.get("humedad_media"),
                humedadMax    = v.get("humedad_max"),
                horMinHumMax  = HistoricService._horas_pico(horas_pico, "hora_humedad_max"),
                humedadMin    = v.get("humedad_min"),
                horMinHumMin  = HistoricService._horas_pico(horas_pico, "hora_humedad_min"),
                velViento     = v.get("vel_viento"),
                velVientoMax  = v.get("vel_viento_max"),
                precipitacion = v.get("precipitacion"),
                etpMon        = v.get("etp_mon"),
                pepMon        = v.get("pep_mon"),
                radiacion     = v.get("radiacion"),
                estacion      = v.get("estacion"),
                provincia     = v.get("provincia"),
                fecha         = v.get("fecha"),
                estaciones    = HistoricService._estaciones_usadas(data, estacion_id),
            )
            for v in data.get("valores_diarios", [])
        ]

    @staticmethod
    def _build_historico_semana(data: dict, estacion_id) -> list:
        """Construye DTOs semanales."""
        horas_pico = data.get("horas_pico", {})
        return [
            HistSemanasDTO(
                anio          = v.get("anio"),
                semana        = v.get("semana"),
                tempMedia     = v.get("temp_media"),
                tempMax       = v.get("temp_max"),
                tempMin       = v.get("temp_min"),
                diaHoraTempMax = HistoricService._horas_pico(horas_pico, "hora_temp_max"),
                diaHoraTempMin = HistoricService._horas_pico(horas_pico, "hora_temp_min"),
                humedadMedia  = v.get("humedad_media"),
                humedadMax    = v.get("humedad_max"),
                humedadMin    = v.get("humedad_min"),
                diaHoraHumMax = HistoricService._horas_pico(horas_pico, "hora_humedad_max"),
                diaHoraHumMin = HistoricService._horas_pico(horas_pico, "hora_humedad_min"),
                velViento     = v.get("vel_viento"),
                velVientoMax  = v.get("vel_viento_max"),
                precipitacion = v.get("precipitacion"),
                etpMon        = v.get("etp_mon"),
                pepMon        = v.get("pep_mon"),
                estacion      = v.get("estacion"),
                radiacion     = v.get("radiacion"),
                estaciones    = HistoricService._estaciones_usadas(data, estacion_id),
                provincia     = v.get("provincia")
            )
            for v in data.get("valores_semanales", [])
        ]

    # -------------------------------------------------------------------------
    # Helpers internos de flujo
    # -------------------------------------------------------------------------

    @staticmethod
    def _pending_dto(tipo: TipoHistorico, estado: dict | None = None) -> ProcesoIngestaDTO:
        return ProcesoIngestaDTO(
            status            = estado['status'] if estado else 'PENDING',
            datos_solicitados = tipo.value,
            started_at        = datetime.now(),
            finished_at       = None,
            error             = None,
        )

    @staticmethod
    def _crear_ingesta_y_lanzar_hilo(
        app,
        tipo: TipoHistorico,
        fec_init: datetime,
        fec_fin: datetime,
        codigo_estacion: Optional[str],
        provincia_id: Optional[str],
        fec_fin_hilo: datetime
    ) -> ProcesoIngestaDTO:
        """Registra estado PENDING y arranca el hilo de ingesta."""
        cursor = fec_init
        while cursor <= fec_fin_hilo:
            IngestaDAO.create(
                status        = 'PENDING',
                dataset       = 'historico',
                tipo          = tipo.value,
                year          = cursor.year,
                month         = cursor.month,
                day           = cursor.day,
                zona          = "provincia" if provincia_id else "estacion",
                started_at    = datetime.now(),
                finished_at   = None,
                error_message = None,
                codigo        = codigo_estacion if codigo_estacion else provincia_id
            )
            cursor += timedelta(days=1)
        lanzar_ingesta_background(
            app,
            IngestionService.ingest_siar_data,
            codigo_estacion,
            provincia_id,
            tipo,
            fec_init,
            fec_fin_hilo
        )
        return HistoricService._pending_dto(tipo)

    @staticmethod
    def _leer_datos_ready(
        tipo: TipoHistorico,
        estacion_id: Optional[int],
        provincia_id: Optional[str],
        fec_init: datetime,
        fec_fin: datetime
    ):
        """Obtiene datos de BD y construye los DTOs cuando el estado es READY."""
        provincia_id = HistoricDAO.obtener_id_provincia_por_str(provincia_id=provincia_id)

        dao_fn, build_fn_name, _ = _TIPO_CONFIG.get(tipo, (None, None, None))
        if not dao_fn:
            raise NotImplementedError(f"Tipo {tipo} no implementado")

        build_fn = getattr(HistoricService, build_fn_name)
        data     = dao_fn(estacion_id, provincia_id, fec_init, fec_fin)
        items    = build_fn(data, estacion_id)

        return HistoricService.comprobar_devolucion(estacion_id, provincia_id, tipo, items)

    # -------------------------------------------------------------------------
    # Helper punto de entrada
    # -------------------------------------------------------------------------
    
    @staticmethod
    def _agrupar_dias_contiguos(dias: list) -> list[tuple]:
        """Agrupa una lista de fechas en rangos contiguos.
        Ej: [19, 21, 22, 25] → [(19,19), (21,22), (25,25)]
        """
        if not dias:
            return []
        
        dias_ordenados = sorted(dias)
        rangos = []
        inicio = dias_ordenados[0]
        fin = dias_ordenados[0]

        for dia in dias_ordenados[1:]:
            if dia - fin == timedelta(days=1):  # contiguo
                fin = dia
            else:  # hueco → cierra rango actual y abre uno nuevo
                rangos.append((inicio, fin))
                inicio = dia
                fin = dia
        
        rangos.append((inicio, fin))
        return rangos

    # -------------------------------------------------------------------------
    # Punto de entrada principal
    # -------------------------------------------------------------------------

    @staticmethod
    def get_historico(
        app,
        tipo: TipoHistorico,
        fec_init: datetime,
        fec_fin: datetime,
        provincia_id: Optional[str] = None,
        codigo_estacion: Optional[str] = None
    ):
        if not (codigo_estacion or provincia_id):
            raise ValueError("Debe indicarse la estación o provincia")

        estacion_id = None
        provincia_db_id = None
        if codigo_estacion:
            estacion_id = HistoricDAO.obtener_id_estacion_por_str(codigo_estacion)
        elif provincia_id:
            provincia_db_id = HistoricDAO.obtener_id_provincia_por_str(provincia_id)

        # 1. Ver qué días ya tenemos en BD
        dias_existentes = HistoricDAO.obtener_dias_existentes(
            tipo, estacion_id, provincia_db_id, fec_init, fec_fin
        )

        # Obtengo los dias sin datos almacenados sobre el rango de fechas indicado
        # (dias_existentes contiene objetos date; comparamos por date() para evitar
        # que un datetime nunca case con un date aunque sea el mismo día)
        dias_faltantes = []
        cursor = fec_init
        while cursor <= fec_fin:
            if cursor.date() not in dias_existentes:
                dias_faltantes.append(cursor)
            cursor += timedelta(days=1)

        # 2. Si no faltan días, leer directamente de BD
        if not dias_faltantes:
            return HistoricService._leer_datos_ready(
                tipo, estacion_id, provincia_id, fec_init, fec_fin
            )

        # 3. Itero sobre los rangos de fechas faltantes definidos
        if dias_faltantes:
            # Obtengo los rangos de fechas ordenados como tuplas
            rangos = HistoricService._agrupar_dias_contiguos(dias_faltantes)
            
            for fec_init_gap, fec_fin_gap in rangos:
                estado = IngestaDAO.obtener_estado(
                    dataset = 'historico',
                    tipo    = tipo.value,
                    year    = fec_init_gap.year,
                    month   = fec_init_gap.month,
                    day     = fec_init_gap.day,
                    zona    = "provincia" if provincia_id else "estacion",
                    error   = None,
                    codigo  = codigo_estacion if codigo_estacion else provincia_id
                )
                
                if estado and estado['status'] in ('PENDING', 'LOADING'):
                    continue  # este rango ya está en proceso, saltarlo
                
                HistoricService._crear_ingesta_y_lanzar_hilo(
                    app, tipo, fec_init_gap, fec_fin,
                    codigo_estacion, provincia_id,
                    fec_fin_hilo=fec_fin_gap
                )
        
        return HistoricService._pending_dto(tipo)

    # -------------------------------------------------------------------------
    # Utilidades
    # -------------------------------------------------------------------------

    @staticmethod
    def comprobar_devolucion(
        estacion_id: Optional[int],
        provincia_id: Optional[int],
        tipo: TipoHistorico,
        datos
    ) -> ProvinciaHistDTO | EstacionHistDTO:
        if provincia_id:
            return ProvinciaHistDTO(type=tipo, datos=datos)
        if estacion_id:
            return EstacionHistDTO(type=tipo, datos=datos)
        raise ValueError("Se debe proporcionar estacion_id o provincia_id")