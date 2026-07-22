# 🌾 Agro-Predict - Data Service

[![Python application](https://github.com/agro-predict-tfg-2026/data-service/actions/workflows/pipeline.yml/badge.svg)](https://github.com/agro-predict-tfg-2026/data-service/actions/workflows/pipeline.yml)
[![Docker](https://img.shields.io/badge/docker-available-blue)](https://hub.docker.com/repository/docker/agropredict/data-service)

**Data Service** es el componente central de almacenamiento y agregación de datos del ecosistema **Agro-Predict**. Este microservicio se encarga de:

- Solicitar, normalizar y almacenar datos de múltiples fuentes externas (clima, plagas, sensores IoT).
- Exponer una API REST unificada para consultar datos históricos, pronósticos, información de cultivos y sensores.
- Gestionar la ingesta asíncrona y reintentos de peticiones fallidas.
- Proveer metadatos de parcelas, dispositivos y sensores.

---

## 🚀 Características principales

- **Fuentes de datos integradas**:
  - 🌦️ [AEMET](https://github.com/agro-predict-tfg-2026/Aemet) (pronósticos)
  - 📊 [SiAR](https://github.com/agro-predict-tfg-2026/SiAR) (datos históricos)
  - 🐛 [ITACyL](https://github.com/agro-predict-tfg-2026/ITACyL) (plagas y calendarios)
  - 📡 **DTAgro** (sensores IoT)
- **Base de datos**: MySQL / MariaDB con SQLAlchemy ORM.
- **Tareas asíncronas**: Celery + RabbitMQ + Redis.
- **Autenticación**: Keycloak (JWT).
- **Documentación interactiva**: Swagger UI (`/api/v1/ui`).
- **Testing**: Pytest + cobertura.
- **CI/CD**: GitHub Actions → construcción y publicación de imagen Docker.
- **Despliegue**: Contenedor Docker listo para usar.

---

## 🏗️ Arquitectura general

```text
data-service/
├── app/ # Código principal de la aplicación
│ ├── init.py # Fábrica de la aplicación Flask
│ ├── extensions.py # Extensiones de Flask (db, celery, swagger)
│ ├── models.py # Modelos SQLAlchemy
│ │
│ ├── clients/ # Clientes HTTP para servicios externos
│ │ ├── base_client.py # Cliente base con lógica de requests
│ │ ├── aemet_client.py # Cliente para AEMET
│ │ ├── siar_client.py # Cliente para SiAR
│ │ ├── itacyl_client.py # Cliente para ITACyL
│ │ └── sensor_client.py # Cliente para DTAgro
│ │
│ ├── ingesta/ # Servicios de ingesta de datos
│ │ ├── ingesta_service.py # Fachada principal de ingesta
│ │ ├── ingesta_dao.py # Acceso a datos de ingesta
│ │ ├── ingesta_dto.py # DTOs de proceso de ingesta
│ │ ├── ingesta_thread.py # Lanzador de hilos en segundo plano
│ │ ├── siar_ingestion_service.py # Ingesta de SiAR
│ │ ├── aemet_ingestion_service.py # Ingesta de AEMET
│ │ ├── itacyl_ingestion_service.py # Ingesta de ITACyL
│ │ ├── sensor_ingestion_service.py # Ingesta de sensores
│ │ └── metadata_ingestion_service.py # Ingesta de metadatos
│ │
│ ├── historicos/ # Datos climáticos históricos
│ │ ├── routes.py # Endpoints /climate/historical/*
│ │ ├── historico_service.py # Lógica de negocio
│ │ ├── historico_dao.py # Consultas a BD
│ │ ├── historico_dto.py # DTOs de respuesta
│ │ └── tasks.py # Tareas Celery para reintentos
│ │
│ ├── forecast/ # Pronósticos meteorológicos
│ │ ├── routes.py # Endpoints /climate/pronostico/*
│ │ ├── forecast_service.py # Lógica de negocio
│ │ ├── forecast_dao.py # Consultas a BD
│ │ └── forecast_dto.py # DTOs de respuesta
│ │
│ ├── cultivos/ # Gestión de cultivos
│ │ ├── routes.py # Endpoints /crop/*
│ │ ├── cultivos_dto.py # DTOs de cultivos, variedades, umbrales
│ │ ├── services/ # Servicios de cultivos
│ │ └── daos/ # Acceso a datos de cultivos
│ │
│ ├── plagas/ # Gestión de plagas
│ │ ├── routes.py # Endpoints /climate/plagas
│ │ ├── plagas_service.py # Lógica de negocio
│ │ ├── plagas_dao.py # Consultas a BD
│ │ └── plagas_dto.py # DTOs de plagas y calendarios
│ │
│ ├── sensores/ # Datos de sensores IoT
│ │ ├── routes.py # Endpoints /sensores
│ │ ├── sensores_service.py # Lógica de negocio
│ │ ├── sensores_dao.py # Consultas a BD
│ │ └── sensores_dto.py # DTOs de sensores
│ │
│ ├── metadata/ # Metadatos (parcelas, dispositivos)
│ │ ├── routes.py # Endpoints /metadatos/*
│ │ ├── metadata_service.py # Lógica de negocio
│ │ ├── metadata_dao.py # Consultas a BD
│ │ └── metadata_dto.py # DTOs de metadatos
│ │
│ ├── auth/ # Autenticación Keycloak
│ │ └── keycloak_service.py # Integración con Keycloak
│ │
│ ├── decorator/ # Decoradores personalizados
│ │ ├── log_decorator.py # Logging de peticiones
│ │ └── token_decorator.py # Validación de JWT
│ │
│ ├── globals/ # Utilidades globales
│ │ ├── dto2dict.py # Conversión de DTOs a JSON
│ │ ├── convertidor_tipo.py # Conversión de tipos (enums, fechas)
│ │ └── normalizar_json.py # Normalización de respuestas JSON
│ │
│ ├── external_services/ # Fachadas de servicios externos
│ │ ├── aemet_service.py
│ │ ├── siar_service.py
│ │ ├── itacyl_service.py
│ │ └── dtagro_service.py
│ │
│ ├── external_communication/ # Comunicación con RabbitMQ
│ │ ├── rabbitmq_config.py
│ │ ├── rabbitmq_send.py
│ │ └── rabbitmq_receive.py
│ │
│ ├── data/ # Datos semilla (JSON, CSV)
│ │ ├── cultivos_horas_frio.json
│ │ ├── location_altitudes.json
│ │ ├── parcelas/
│ │ ├── sensores/
│ │ └── registros_plagas/
│ │
│ └── tests/ # Pruebas unitarias e integración
│ ├── conftest.py
│ └── historicos/
│ ├── test_dao.py
│ ├── test_service.py
│ ├── test_routes.py
│ └── test_tasks.py
│
├── config/ # Configuración de la aplicación
│ └── config.py # Configs por entorno (dev, test, prod)
│
├── migrations/ # Migraciones de base de datos (Alembic)
│
├── scripts/ # Scripts utilitarios
│ ├── init_db.py # Inicialización de BD
│ └── insert_data.py # Carga de datos iniciales
│
├── swagger/ # Documentación OpenAPI
│ └── swagger.yml
│
├── helpers/ # Utilidades y excepciones
│ ├── ApiExceptions.py
│ ├── aemet_parser.py
│ └── siar_exceptions.py
│
├── dockerfile # Instrucciones para construir la imagen
├── entrypoint.sh # Punto de entrada del contenedor
├── entrypoint.py # Arranque de la aplicación
├── celery_worker.py # Worker de Celery
├── requirements.txt # Dependencias del proyecto
├── pyproject.toml # Configuración de pytest y coverage
├── .github/workflows/ # Pipelines de CI/CD
└── README.md # Este archivo
```

---

## 📚 Documentación adicional

- [Bases de datos y colas](docs/databases.md): qué servicio usa MySQL, Redis y RabbitMQ, por qué, y cómo se encolan/borran los reintentos pendientes de SiAR.

---

## 🛠️ Instalación y ejecución

### Requisitos previos

- Python 3.13 (obligatorio; versiones más nuevas como 3.14 aún no tienen wheels de Windows precompilados para dependencias como `python-qpid-proton`, lo que obliga a compilar desde el código fuente)
- MySQL / MariaDB
- RabbitMQ
- Redis
- Docker (opcional)

### Instalación local

1. Clonar el repositorio

```bash
git clone https://github.com/quercus-uex/agro-predict-data-service.git
cd agro-predict-data-service
```

2. Crear entorno virtual

```bash
py -3.13 -m venv venv
```

3. Activar entorno virtual

```bash
# Windows:
venv\Scripts\activate

# Linux:
source venv/bin/activate
```

4. Instalar dependencias

```bash
pip install -r requirements.txt
```

5. Configurar variables de entorno (crear archivo .env)

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

6. Inicializar base de datos

```bash
python scripts/init_db.py
```

7. Ejecutar la aplicación

```bash
python entrypoint.py
```

8. En otra terminal, ejecutar el worker de Celery

```bash
celery -A celery_worker:celery_app worker --loglevel=info
```

### Ejecución en Docker

```bash
# Construir la imagen
docker build -t agro-predict-data-service .

# Ejecutar el contenedor
docker run -p 5000:5000 --env-file .env agro-predict-data-service
````

## Endpoints principales - API

#### Datos históricos por provincias

```http
  GET /climate/historical/provincias
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `api_key` | `string` | **Required**. Your API key |

#### Get item

```http
  GET /api/items/${id}
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `id`      | `string` | **Required**. Id of item to fetch |

#### add(num1, num2)

Takes two numbers and returns the sum.

## 🧪 Ejecutar pruebas

Para ejecutar pruebas unitarias y de integración, utiliza los siguientes comandos:

```bash
# Ejecutar todas las pruebas
pytest

# Con cobertura
pytest --cov=app/historicos --cov-fail-under=80

# Pruebas específicas
pytest app/tests/historicos/
```

## 🤝 Como contribuir

### 1. **Haz FORK del repositorio**

### 2. **Crea una rama para tu FEATURE**:

```bash
git checkout -b feature/nueva-funcionalidad
```

### 3. **Realiza tus cambios aplicando las siguientes convenciones**:

    - Añade pruebas para nueva funcionalidad
    - Asegura que todas las pruebas pasan (`pytest`)
    - Actualiza la documentación si es necesario

### 4. **Haz commit de los cambios**:

```bash
git commit -m "feat: añadir nueva funcionalidad X"
```

### 5. **Sube los cambios a tu FORK**:

```bash
git push origin feature/nueva-funcionalidad
```

### 6. **Abre una PULL REQUEST contra la rama `main`**

### Convenciones de código

- Usa tipado estático en todas las funciones
- Documenta las nuevas funciones con DockStrings
- Sigue el patrón DTO para las respuestas de la aplicando
- Las excepciones personalizadas heredan de `APIException`

### Reportar issues

Si encuentras un bug o tienes una sugerencia de implementación, pro favor:

#### 1. Verifica que no exista ya en el apartado `issues`.

#### 2. Abre un nuevo issue con:

- Descripción clara del problema o propuesta
- Pasos para reproducir el problema
- Comportamiento esperado vs actual
- Logs o capturas relevantes

## 📄 License

[Apache 2.0 License](https://choosealicense.com/licenses/mit/)

## 📬 Contacto

- **email**: alvaromendobusiness@gmail.com
- **Documentación del proyecto**: [documentacion_agro_predict](https://github.com/agro-predict-tfg-2026/documentacion_agro_predict)
