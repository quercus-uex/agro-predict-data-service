from ...models import CultivoParcela, Cultivo, Parcelas
from sqlalchemy import select, and_
from app.extensions import db
from typing import Optional
from datetime import datetime
from ...globals.row2dict_converter import row2dict_converter

class CultivoParcelaDAO:

    @staticmethod
    def crear_cultivos_asociados_a_parcelas(
        cultivo : Cultivo,
        nombre_parcela : str
    ) -> Optional[CultivoParcela]:
        """
        Se encarga de crear la asociación entre cultivo y parcela

        Args:
            cultivo (Cultivo)
            nombre_parcela (str)

        Returns:
            Optional[CultivoParcela]
        """
        try:
            # Obtención de la parcela asociada al nombre indicado por parámetros
            parcela : Parcelas = db.session.query(Parcelas).filter(
                Parcelas.nombre == nombre_parcela
            ).first()

            if not parcela:
                print(f"La parcela {nombre_parcela} no se encuentra registrada en el sistema")
                return None
            
            # Comprobar previamente que el cultivo no esté ya asociado a la parcela
            existe_asociacion = db.session.query(CultivoParcela).filter(
                CultivoParcela.cultivo_id == cultivo.id,
                CultivoParcela.parcela_id == parcela.public_id,
                CultivoParcela.fecha_fin == None
            ).first()

            if existe_asociacion:
                return None
            
            cultivo_parcela = CultivoParcela(
                cultivo_id = cultivo.id,
                parcela_id = parcela.id,
                fecha_inicio = datetime.today(),
                fecha_fin = None
            )

            db.session.add(cultivo_parcela)
            db.session.commit()

            return cultivo_parcela

        except Exception as e:
            print(f"Error al asociar el cultivo con la parcela : {e}")
            return None

    @staticmethod
    def obtener_asociaciones_cultivo_parcela(
        nombre_cultivo : str,
        parcela_id : str
    ):
        """
        Obtiene los registros de los cultivos que se encuentran asociados a las parcelas

        Args:
            nombre_cultivo (str)
            parcela_id (str)
        
        Returns
            Optional[list[CultivoParcela]]
        """
        try:
            query = (
                select(
                    Cultivo,
                    Parcelas,
                    CultivoParcela.fecha_inicio,
                    CultivoParcela.fecha_fin
                ).join(CultivoParcela, CultivoParcela.cultivo_id == Cultivo.id)
                .join(Parcelas, CultivoParcela.parcela_id == Parcelas.id)
            )

            if nombre_cultivo:
                cultivo = db.session.query(Cultivo).filter(
                    Cultivo.nombre == nombre_cultivo
                ).first()

                query = query.where(CultivoParcela.cultivo_id == cultivo.id)

            if parcela_id:
                query = query.where(Parcelas.public_id == parcela_id)
            
            return db.session.execute(query).all()
        
        except Exception as e:
            print(f"Error real : {e}")
            return None
