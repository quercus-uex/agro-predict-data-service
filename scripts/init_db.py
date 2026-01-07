import sys, os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from insert_data import job

# Configuracion del logging
logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

# Inicialización de la estructura de la base de datos
with app.app_context():
    try:
        logger.info("Verificando conexión a la base de datos...")
        
        # Verificar conexión
        connection = db.engine.connect()
        logger.info("Conexión establecida correctamente")
        connection.close()
        
        # Eliminar tablas existentes (para desarrollo)
        #logger.info("Eliminando tablas existentes...")
        #db.drop_all()
        #logger.info("Tablas eliminadas")
        
        # Crear todas las tablas
        logger.info("Creando tablas...")
        db.create_all()
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
