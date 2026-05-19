"""
Extensiones de Flask
"""
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
from flask import jsonify
from flask_migrate import Migrate
from keycloak import KeycloakOpenID
from celery import Celery, Task
import yaml
import pathlib

# -------------------------------------------------------------------------
# Instancias de clases
# -------------------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate() # Aplico migracionnes de Alembic
celery_app = Celery()

# -------------------------------------------------------------------------
# Inicializador de dependencias
# -------------------------------------------------------------------------
def init_extensions(app):
    """Inicializo las extensiones con la aplicación Flask"""
    db.init_app(app)
    migrate.init_app(app, db)
    register_swagger(app)
    register_keyclaok(app)
    celery_init_app(app)

# -------------------------------------------------------------------------
# Configuraciones de extensiones específicas
# -------------------------------------------------------------------------
def register_keyclaok(app):
    global keycloak_openid
    keycloak_openid = KeycloakOpenID(
        server_url = app.config['KEYCLOAK_SERVER_URL'],
        realm_name = app.config['KEYCLOAK_REALM_NAME'],
        client_id = app.config['KEYCLOAK_CLIENT_ID'],
        #cert = app.config['KEYCLOAK_CERT'],
        client_secret_key = app.config['KEYCLOAK_CLIENT_SECRET'] 
    )

def register_swagger(app):
    """
    Registra el blueprint de swagger junto con su configuración para poder usarlo
    """
    swagger_ui_blueprint = get_swaggerui_blueprint(
        app.config['SWAGGER_URL'],
        app.config['API_URL'],
        config = {
            'app_name' : app.config['SERVICE_NAME'],
            'docExpansion' : 'none'
        } 
    )

    app.register_blueprint(
        swagger_ui_blueprint, 
        url_prefix = app.config['SWAGGER_URL']
    )

    @app.route(app.config['API_URL'])
    def serve_swagger_json():
        try:
            swagger_path = pathlib.Path(__file__).parent.parent / 'swagger/swagger.yml'
            print(f"Swagger path : {swagger_path}")
            with open(swagger_path, encoding = 'utf-8') as file:
                swagger_spec = yaml.safe_load(file)
                return jsonify(swagger_spec)
        except Exception as e:
            app.logger.error(f"Error cargando swagger.yml : {e}")
            return jsonify(
                {
                    "error" : "No se pudo cargar la especificación Swagger",
                    "details" : str(e)
                }
            ), 500

def celery_init_app(app) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.config_from_object(app.config["CELERY"])
    celery_app.Task = FlaskTask

    app.extensions['celery'] = celery_app

    return celery_app