from .daos.cultivos_dao import CultivosDAO
from app import create_app
import os
import json


class SeedIngestService:
    """
    Clase de inicialización sobre tablas estructurales de dominio (Cultivos, Variedades, 
    Umbrales, Modelos de horas-frio, Etapas fenologicas)

    Se ejecuta de forma controlada, en inicializaciones y despliegue.
    """
   
    def main():
        app = create_app()
        with app.app_context():
            try:
                BASE_DIR = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(BASE_DIR, "..", "data", "cultivos_horas_frio.json")
                with open(file_path, 'r', encoding = "utf-8") as f:
                    datos = json.load(f)

                # Inserción de modelos de horas de frio
                modelos = datos['modelos_horas_frio']
                for modelo in modelos:
                    m = CultivosDAO.crear_modelos_horas_frio(
                        nombre = modelo['nombre'],
                        codigo = modelo['codigo'],
                        descripcion = modelo['descripcion']
                    )

                    if not m:
                        raise Exception(f'No se ha podido insertar el modelo {m}')
                    
                # Inserción de etapas fenologicas
                etapas = datos['etapas_fenologicas']
                for etapa in etapas:
                    e = CultivosDAO.crear_estados_fenologicos(
                        nombre = etapa['nombre'],
                        codigo = etapa['codigo'],
                        orden = etapa['orden']
                    )

                    if not e:
                        raise Exception(f'No se ha podido insertar la etapa {e}')
                    
                # Inserción de cultivos, sus variedades y sus umbrales
                cultivos = datos['cultivos']
                for cultivo in cultivos:
                    
                    c = CultivosDAO.crear_cultivo(
                        nombre = cultivo['nombre'],
                        nombre_cientifico = cultivo['nombre_cientifico'],
                        descripcion = cultivo['descripcion'],
                        grupo = cultivo['grupo'],
                    )

                    if not c:
                        raise Exception(f'No se ha podido insertar el cultivo {c}')
                    
                    variedades = cultivo['variedades']
                    for variedad in variedades:
                        
                        v = CultivosDAO.crear_variedad(
                            nombre_variedad = variedad['nombre'],
                            nombre_cultivo_asociado = cultivo['nombre'],
                            horas_frio_min = variedad['horas_frio_min'],
                            horas_frio_max = variedad['horas_frio_max'],
                            nombre_modelo_horas_frio = variedad['modelo_horas_frio']
                        )

                        if not v:
                            raise Exception(f'No se ha podido insertar la variedad {v}')
                        
                        umbrales = variedad['umbrales']
                        for umbral in umbrales:
                            u = CultivosDAO.crear_umbrales_temperatura(
                                nombre_variedad = variedad['nombre'],
                                nombre_etapa_fenologica = umbral['etapa'],
                                umbrales_criticidad = {
                                    'critico': umbral['critico'], 
                                    'alto': umbral['alto'], 
                                    'moderado': umbral['moderado'], 
                                    'bajo': umbral['bajo']
                                }
                            )

                            if not u:
                                raise Exception(f"No se ha podido insertar el umbral {u}")
                



            except Exception as e:
                print(f"Algo ha salido mal procesando los datos de ingesta de cultivos : {e}")
                return None


if __name__ == '__main__':
    SeedIngestService.main()