#!/bin/bash

echo "Inicializando la base de datos..."
python scripts/init_db.py

echo "Arrancando el servicio..."
python entrypoint.py