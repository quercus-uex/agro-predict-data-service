import sys, os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from flask_migrate import upgrade, stamp
from app.extensions import db

# Configuracion del logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

# Inicialización de la estructura de la base de datos
with app.app_context():
    try:
        from insert_data import job
        logger.info("Verificando conexión a la base de datos...")
        
        # Verificar conexión
        connection = db.engine.connect()
        logger.info("Conexión establecida correctamente")
        connection.close()
        
        # Crear todas las tablas
        logger.info("Creando tablas...")
        inspector = db.inspect(db.engine)
        tablas_existentes = set(inspector.get_table_names()) - {"alembic_version"}
        if tablas_existentes:
            # La base de datos ya tiene tablas de la aplicación: aplico las
            # migraciones pendientes de forma incremental
            upgrade()
        else:
            # Base de datos nueva y vacía (o con un "alembic_version" huérfano
            # de un intento anterior fallido): la cadena de migraciones asume
            # que las tablas base ya existen (solo contiene ALTER TABLE),
            # así que las creo a partir de los modelos actuales y marco
            # la base de datos como si ya estuviera al día ("head"),
            # sin volver a ejecutar las migraciones antiguas
            db.create_all()
            stamp()
        logger.info("Tablas creadas exitosamente")
        
        # Verificar que las tablas se crearon
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"Tablas creadas: {', '.join(tables)}")

        logger.info("Insertar datos SiAR en tablas")
        job(app)
        logger.info("Datos insertados correctamente")
        
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        logger.info("Cerrando conexiones...")
        db.session.remove()
        db.engine.dispose()
        logger.info("Proceso completado")

print("\n=== Base de datos inicializada correctamente ===")
