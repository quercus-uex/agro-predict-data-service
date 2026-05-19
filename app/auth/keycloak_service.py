import requests
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class KeyCloakService:
    def __init__(self, app):
        self.server_url = app.config.get('KEYCLOAK_SERVER_URL')
        self.realm_name = app.config.get('KEYCLOAK_REALM_NAME')
        #self.client_id = app.config.get('KEYCLOAK_CLIENT_ID')
        #self.cert = app.config.get('KEYCLOAK_CERT')
        #self.client_secret_key = app.config.get('KEYCLOAK_CLIENT_SECRET')
    

    def generic_communication(
        self,
        args: dict,
        tipo: str
    ) -> Optional[Dict]:
        try:
            client_id = args.get('client_id')
            client_secret = args.get('client_secret')

            base_url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/"

            if tipo == "token": 
                url = base_url + "token"
            elif tipo == "validar":
                url = base_url + "token/introspect"
            else:
                raise ValueError(f"Tipo de operación desconocido: {tipo}")

            response = requests.post(
                url=url,
                data=args.get('payload'),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                auth=(client_id, client_secret) if tipo == "validar" else None,
                verify=False,
                timeout=10
            )

            response.raise_for_status()

            return response.json()

        except requests.HTTPError as e:
            logger.error(f"Error HTTP comunicándose con Keycloak: {e}")
            return None
        except Exception as e:
            logger.error(f"Error comunicándose con Keycloak: {e}")
            return None


    def _get_token(self, username: str, password: str) -> Optional[str]:
        args = {
            'client_id': self.client_id,
            'client_secret': None,  # curl-client es público, no tiene secret
            'payload': {
                'grant_type': 'password',
                'client_id': self.client_id,
                'username': username,
                'password': password,
                'scope': 'openid'
            }
        }

        token_data = self.generic_communication(args=args, tipo="token")

        if token_data:
            return token_data.get('access_token')
        return None


    def _validar_token(self, token: str, client_id: str, client_secret: str) -> Optional[Dict]:
        args = {
            'client_id': client_id,
            'client_secret': client_secret,
            'payload': {
                'token': token
            }
        }

        result = self.generic_communication(args=args, tipo="validar")

        if result and result.get('active'):
            return result
        return None