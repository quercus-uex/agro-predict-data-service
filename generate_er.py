from sqlalchemy import create_engine, MetaData
from eralchemy import render_er

# Conexión a MariaDB
engine = create_engine(
    "mysql+pymysql://mendo:12345@localhost:3307/tfg"
)

# Reflejar estructura de la base de datos
metadata = MetaData()
metadata.reflect(bind=engine)

# Generar diagrama
render_er(metadata, "diagrama.png")

print("Diagrama generado correctamente.")