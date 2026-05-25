from app.extensions import celery_app
from datetime import date
import logging
import redis
import json
import os
from dotenv import load_dotenv
from ..ingesta.siar_ingestion_service import SiarIngestionService
from .historico_dto import TipoHistorico

load_dotenv()
logger = logging.getLogger(__name__)
r = redis.Redis(
    host     = os.getenv('REDIS_HOST', 'localhost'),
    port     = int(os.getenv('REDIS_PORT', 6379)),
    db       = int(os.getenv('REDIS_DB', 0)),
    username = os.getenv('REDIS_USER'),
    password = os.getenv('REDIS_PASS'),
    decode_responses = True
)
PENDING_TASKS_PREFIX = "siar:pending:"

def _build_key(tipo: str, zona: str, fec_init: str, fec_fin: str) -> str:
    """
    Construye la clave Redis que identifica unívocamente una tarea pendiente.
    Formato: siar:pending:{tipo}:{zona}:{fec_init}:{fec_fin}
    """
    return f"{PENDING_TASKS_PREFIX}{tipo}:{zona}:{fec_init}:{fec_fin}"


@celery_app.task
def programar_consulta_datos_task(args: dict):
    """
    Encola en Redis una consulta fallida (400) para reintentarla más tarde.
    args debe contener: tipo, codigo_estacion_id, codigo_provincia_id, fec_init, fec_fin
    """
    try:
        logger.info("=== Encolando tarea pendiente en Redis ===")

        tipo   = args['tipo']
        zona   = args.get('codigo_provincia_id') or args.get('codigo_estacion_id')
        fec_init = args['fec_init']
        fec_fin  = args['fec_fin']

        key = _build_key(tipo, zona, fec_init, fec_fin)

        # Si ya existe esa tarea exacta, no la duplicamos
        if r.exists(key):
            logger.info(f"Tarea ya pendiente, ignorando duplicado: {key}")
            return {"status": "ALREADY_QUEUED", "key": key}

        r.set(key, json.dumps(args))
        logger.info(f"Tarea encolada: {key}")

        return {"status": "QUEUED", "key": key}

    except Exception as e:
        logger.error(f"Error encolando tarea: {e}")
        raise


@celery_app.task
def procesar_cola_pendientes_task():
    """
    Recorre todas las tareas pendientes en Redis y las reintenta.
    Llamada desde un endpoint manual.
    """
    keys = r.keys(f"{PENDING_TASKS_PREFIX}*")
    if not keys:
        return {}
    logger.info(f"=== Procesando cola pendiente: {len(keys)} tareas ===")

    resultados = {"ok": [], "failed": [], "skipped": []}

    for key in keys:
        raw = r.get(key)
        if not raw:
            continue

        args = json.loads(raw)
        tipo         = args['tipo']
        fec_init_str = args['fec_init']
        fec_fin_str  = args['fec_fin']

        try:
            fec_init = date.fromisoformat(fec_init_str)
            fec_fin  = date.fromisoformat(fec_fin_str)

            lista_datos = SiarIngestionService.ingest_siar_data(
                codigo_estacion_id  = args.get('codigo_estacion_id'),
                codigo_provincia_id = args.get('codigo_provincia_id'),
                tipo                = TipoHistorico[tipo.upper()],
                fec_init            = fec_init,
                fec_fin             = fec_fin,
            )

            # Si llegamos aquí sin excepción y con datos, eliminamos la tarea pendiente
            if lista_datos:
                r.delete(key)
                logger.info(f"Tarea completada y eliminada: {key}")
                resultados["ok"].append(key)
            else:
                logger.info(f"Tarea sin datos aún, se mantiene pendiente: {key}")
                resultados["skipped"].append(key)

        except Exception as e:
            logger.error(f"Tarea {key} falló de nuevo: {e}")
            resultados["failed"].append({"key": key, "error": str(e)})

    return resultados