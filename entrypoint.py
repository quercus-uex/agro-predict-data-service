# Punto de entrada de la aplicación. Se crea la aplicación y se lanza el servidor de desarrollo
from app import create_app
from config import config

def main():
    # Creación de la configuración de la aplicación
    app = create_app()

    # Información inicial, mostrada por consola
    print("🚀 Servicio de datos iniciado")
    print("🌐 Url: http://localhost:5000")
    # Ejecución del servidor de la aplicación
    app.run(host='0.0.0.0', port=5000, debug=config.config['development'])

if __name__ == '__main__':
    main()