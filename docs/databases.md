# Bases de datos y colas del Data Service

Este documento describe qué almacén de datos usa cada servicio del Data Service (AEMET, SiAR, ITACyL/plagas, DTAgro/sensores, cultivos, metadatos), por qué, y los puntos clave de su ciclo de vida.

El servicio usa tres almacenes con roles completamente distintos:

| Almacén | Rol | Contenido |
| :--- | :--- | :--- |
| **MySQL / MariaDB** | Base de datos de negocio (persistencia definitiva) | Datos climáticos, pronósticos, cultivos, plagas, sensores, metadatos, y el **estado de cada proceso de ingesta** |
| **Redis** | Backend de Celery + cola de reintentos pendientes | Resultados de tareas Celery, claves `siar:pending:*` (solo SiAR) |
| **RabbitMQ** | Broker de mensajería | Transporte de tareas Celery (`broker_url`); wrapper pub/sub propio, actualmente sin usar |

---

## MySQL / MariaDB — almacenamiento principal de todos los servicios

- **Configuración**: `SQLALCHEMY_DATABASE_URI` en [config/config.py](../config/config.py), definida por `SQLALCHEMY_DATABASE_URL` en `.env` (ver [.env.example](../.env.example)). En tests se sustituye por SQLite en memoria (`TEST_DATABASE_URL`).
- **Acceso**: SQLAlchemy vía Flask-SQLAlchemy (`app/extensions.py`), con migraciones Alembic en `migrations/`.
- **Por qué**: es el único almacén con garantías ACID y consultas relacionales del proyecto; todo dato que debe sobrevivir reinicios y ser consultable por la API pasa por aquí. Cada servicio de ingesta (`app/ingesta/*_ingestion_service.py`) termina escribiendo en MySQL a través de su DAO correspondiente.

### DAOs y datos por servicio

| Servicio / fuente | DAO | Modelos principales (`app/models.py`) |
| :--- | :--- | :--- |
| SiAR (histórico climático) | `app/historicos/historico_dao.py` | `MedicionClimatica`, `Estacion`, `Provincia` |
| AEMET (pronóstico) | `app/forecast/forecast_dao.py` | `Predicciones`, `LocalidadesClimaticas`, `Localidades` |
| ITACyL (plagas y calendarios) | `app/plagas/plagas_dao.py` | `Plaga`, `CalendarioPlaga` |
| DTAgro (sensores IoT) | `app/sensores/sensores_dao.py` | `Sensores`, `Dispositivos`, `MedicionesSensor` |
| Cultivos | `app/cultivos/daos/*` | `Cultivo`, `Variedades`, `UmbralesTemperatura`, `CultivoParcela`, `CultivoPlaga` |
| Metadatos (parcelas, dispositivos) | `app/metadata/metadata_dao.py` | `Parcelas`, `Dispositivos`, `Metadatos` |
| **Estado de ingesta (todos)** | `app/ingesta/ingesta_dao.py` | `IngestaStatus` |

Los DAOs son la única capa que toca `db.session` directamente; los `*_service.py` de negocio y las `routes.py` no hacen SQL.

### `IngestaStatus`: seguimiento común a todos los servicios de ingesta

La tabla `ingesta_status` (modelo `IngestaStatus` en `app/models.py:152`) es el mecanismo compartido por **todos** los servicios de ingesta (SiAR, AEMET, ITACyL, sensores) para registrar el progreso de cada petición: `dataset`, `tipo`, `zona`/`codigo`, fecha y `status` (`LOADING`, `READY`, `FAILED`, y en el caso de SiAR también `PENDING_RETRY`), junto con `error` y `finish_time`.

Cada `*_ingestion_service.py` sigue el mismo patrón: marca `LOADING` antes de pedir datos al cliente externo, y `READY`/`FAILED` al terminar, capturando la excepción si algo falla:

- `SiarIngestionService.ingest_siar_data` (`app/ingesta/siar_ingestion_service.py`)
- `AemetIngestionService.ingest_aemet_data` (`app/ingesta/aemet_ingestion_service.py`)
- `ItacylIngestionService.ingest_itacyl_data` (`app/ingesta/itacyl_ingestion_service.py`) — este no usa `IngestaStatus`, solo hace `db.session.rollback()` y loguea el error en caso de fallo.
- `SensorIngestionService.ingesta_sensores_data` (`app/ingesta/sensor_ingestion_service.py`) — tampoco usa `IngestaStatus`; solo loguea el error.

**Solo SiAR** distingue un caso de fallo "recuperable" (`SiARFechaInvalidaError`) y lo marca como `PENDING_RETRY`, además de encolar un reintento en Redis (ver siguiente sección). AEMET, ITACyL y sensores no tienen mecanismo de reintento: si fallan, quedan en `FAILED` (o simplemente logueados) y requieren una nueva llamada manual a la ingesta para reintentarse.

---

## Redis — cola de reintentos de SiAR + backend de Celery

- **Configuración**: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_USER`, `REDIS_PASS` en `.env`; usado como `result_backend` de Celery en `config/config.py` y con un cliente `redis.Redis(...)` propio en [app/historicos/tasks.py](../app/historicos/tasks.py).
- **Por qué**: SiAR limita el número de peticiones por minuto y por día. Cuando una consulta falla con un 400 "recuperable" (`SiARFechaInvalidaError`), en vez de perder la petición se guarda en Redis para reintentarla más tarde, sin bloquear el flujo de ingesta principal.
- **Importante**: este mecanismo de cola en Redis es **exclusivo de SiAR**. AEMET, ITACyL y sensores no encolan nada en Redis; sus fallos solo quedan reflejados en `IngestaStatus` (o en logs) y se reintentan volviendo a invocar el endpoint de ingesta correspondiente.
- **Quién escribe (encola)**: `app/ingesta/siar_ingestion_service.py:107-108` llama a `programar_consulta_datos_task.delay(...)`, que en `tasks.py:52` hace:
  ```python
  key = f"siar:pending:{tipo}:{zona}:{fec_init}:{fec_fin}"
  r.set(key, json.dumps(args))
  ```
  Si la clave ya existe, no se duplica (`r.exists(key)` en `tasks.py:48`).
- **Quién lee/reintenta**: `procesar_cola_pendientes_task` (`tasks.py:63`) recorre todas las claves `siar:pending:*`, reintenta cada una vía `SiarIngestionService.ingest_siar_data`, y solo se dispara manualmente desde:
  ```http
  POST /climate/historical/reintentar-pendientes
  ```
  (`app/historicos/routes.py:177-183`). **No hay ningún cron ni scheduler que la invoque automáticamente.**
- **Quién borra**: la propia `procesar_cola_pendientes_task`, y **solo si el reintento devuelve datos** (`tasks.py:99`, `r.delete(key)`). Si sigue sin datos, la clave se mantiene pendiente.
- **Punto clave / riesgo**: las claves se guardan con `r.set` **sin TTL**. Si nadie llama al endpoint de reintento, o si una tarea falla de forma permanente, la clave queda en Redis indefinidamente — no hay expiración automática ni límite de reintentos.

---

## RabbitMQ — broker de Celery (activo) + wrapper pub/sub (inactivo)

RabbitMQ cumple dos roles independientes en el proyecto, y solo uno está realmente en uso:

### 1. Broker de Celery (en uso, común a todos los servicios que disparan tareas asíncronas)

- **Configuración**: `RABBITMQ_CONNECTION` se usa como `broker_url` de Celery en `config/config.py:39`.
- **Por qué**: transporta los mensajes de las tareas Celery (`programar_consulta_datos_task`, `procesar_cola_pendientes_task`) entre la app Flask y el worker (`celery_worker.py`). El *estado* de la cola de reintentos vive en Redis (ver arriba); RabbitMQ solo mueve los mensajes de ejecución de tareas.
- **Relación con los servicios de datos**: es indirecta y, hoy por hoy, solo la usa SiAR — es el único que dispara tareas Celery (`programar_consulta_datos_task` / `procesar_cola_pendientes_task`). AEMET, ITACyL y sensores hacen su ingesta de forma síncrona y no pasan por Celery/RabbitMQ.

### 2. Wrapper pub/sub propio (sin usar actualmente)

- **Código**: `app/external_communication/rabbitmq_config.py`, `rabbitmq_send.py`, `rabbitmq_receive.py`, basado en `pika` con colas `QUEUE_IN_NAME` / `QUEUE_OUT_NAME`.
- **Por qué existía**: pensado para delegar el parseo del texto de AEMET a un servicio externo vía cola (publicar el texto crudo, esperar el JSON procesado).
- **Quién lo usaba**: únicamente `app/external_services/aemet_service.py:69-96`, y ese bloque está **comentado** — el servicio hace fallback directo a `AemetParser.parse(texto, respuesta_queue=False)` (línea 97).
- **Estado actual**: ningún servicio (ni AEMET, ni SiAR, ni ITACyL, ni sensores) usa este wrapper en producción; solo AEMET lo tenía integrado, y está deshabilitado.

---

## Resumen rápido

| Pregunta | Respuesta |
| :--- | :--- |
| ¿Dónde se guardan los datos finales de todos los servicios (SiAR, AEMET, ITACyL, sensores)? | MySQL, vía el DAO de cada módulo |
| ¿Dónde se registra el progreso/estado de cada ingesta (LOADING/READY/FAILED)? | MySQL, tabla `ingesta_status`, para SiAR y AEMET (ITACyL y sensores solo loguean el error) |
| ¿Qué servicio tiene cola de reintentos automatizable? | Solo SiAR, en Redis (claves `siar:pending:*`) |
| ¿Cómo reintentan sus fallos AEMET, ITACyL y sensores? | No tienen cola; hay que volver a invocar manualmente el endpoint de ingesta correspondiente |
| ¿Quién borra las claves de Redis de SiAR? | `procesar_cola_pendientes_task`, solo si el reintento tiene éxito |
| ¿Hay expiración automática de esas claves? | No — sin TTL, requiere reintento manual vía API |
| ¿RabbitMQ almacena datos de algún servicio? | No — solo transporta mensajes de tareas Celery, y solo las que dispara SiAR |
| ¿Se usa el wrapper RabbitMQ pub/sub (`external_communication/`)? | No, está comentado; solo lo usaba AEMET |
