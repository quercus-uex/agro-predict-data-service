# Controlador de HISTORICOS
from __init__ import historic_bp
from globals import log
from flask import request

@historic_bp.route('/climate/historical/provincias')
@log('../logs/fichero_salida.json')
def historicalProvincial():

    province_code = request.args.get('provinceCode', 'CC')
    type = request.args.get('type', 'HORA')
    start_date = request.args.get('startDate', '2025-12-31')
    end_date = request.args.get('endDate', '2025-12-31')

    
    