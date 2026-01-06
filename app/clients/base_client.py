import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class BaseClient:
    def __init__(self, app, service_name : str):
        self.app = app
        self.service_name = service_name
        self.timeout = 10

    def _make_request(
            self,
            method : str,
            url : str,
            **kwargs
        ) -> Optional[requests.Response] :
            """Realiza requests"""

            url = url.strip() # Elimina espacios y caracteres de controla al inicio/final de la url
            print("\n========== REQUEST DEBUG ==========", flush=True)
            print("METHOD:", method, flush=True)
            print("URL:", url, flush=True)
            print("KWARGS:", kwargs, flush=True)

            if "json" in kwargs:
                print("JSON BODY:", kwargs["json"], flush=True)
            if "data" in kwargs:
                print("DATA BODY:", kwargs["data"], flush=True)
            if "params" in kwargs:
                print("QUERY PARAMS:", kwargs["params"], flush=True)

            print("===================================\n", flush=True)

            try: 
                response = requests.request(
                    method = method,
                    url = url,
                    timeout = self.timeout,
                    **kwargs
                )

                return response
            except requests.exceptions.RequestException as e:
                logger.error(f"Ha ocurrido un error con la request a {url}, error: {e}")
                return None