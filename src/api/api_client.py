import logging
import requests
from config_ import Config
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class LuxsClient:
    def __init__(self, environment: str = "Acceptatie"):
        """
        Deze klasse beheert de communicatie met de LUXS API (Acceptatie of Productie).

        Args:
            environment (str): De omgeving om te gebruiken ("Acceptatie" of "Productie")
        """
        logger.debug(f"Initialiseren van de LuxsClient voor {environment} omgeving")

        # 1. Configuratie inladen
        config = Config.load_config()
        logger.debug("Configuratie geladen")

        # 2. Bepaal de juiste configuratiewaarden op basis van de omgeving
        env_prefix = "LUXS_ACCEPT" if environment == "Acceptatie" else "LUXS_PROD"

        # 3. Controleer of alle benodigde configuratiewaarden aanwezig zijn
        required_keys = [
            f"{env_prefix}_API_URL",
            f"{env_prefix}_AUTH_URL",
            f"{env_prefix}_CLIENT_ID",
            f"{env_prefix}_CLIENT_SECRET"
        ]

        logger.debug(f"Benodigde configuratiewaarden: {required_keys}")

        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            error_msg = f"Ontbrekende configuratie voor {environment} omgeving: {', '.join(missing_keys)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 4. Log de geladen configuratie voor debugging
        logger.debug("Geadresseerde configuratie:")
        logger.debug(f"API URL uit config: {config[f'{env_prefix}_API_URL']}")
        logger.debug(f"Auth URL uit config: {config[f'{env_prefix}_AUTH_URL']}")

        # 5. Opslaan van de relevante configuratiewaarden
        self.environment = environment
        self.auth_url = config[f"{env_prefix}_AUTH_URL"]
        self.api_url = config[f"{env_prefix}_API_URL"]
        self.client_id = config[f"{env_prefix}_CLIENT_ID"]
        self.client_secret = config[f"{env_prefix}_CLIENT_SECRET"]
        self.access_token = None

        # 6. Valideer de URLs (moeten HTTPS zijn, etc.)
        if not self._validate_urls():
            raise ValueError(f"Ongeldige URLs in de {environment} configuratie.")

    def authenticate(self) -> str:
        """
        Voer een authenticatie uit met de LUXS API via de
        OAuth2 client-credentials flow.

        Returns:
            str: Access token als authenticatie succesvol is, anders None.
        """
        try:
            # Voorbereiden van de authenticatie aanvraag met client credentials
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }

            # Use the environment-specific auth URL
            response = requests.post(self.auth_url, data=auth_data)

            # Controleer of authenticatie gelukt is
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                logger.info("Authenticatie succesvol")
                return self.access_token
            else:
                logger.error(f"Authenticatie mislukt, statuscode: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Authenticatie mislukt met fout: {str(e)}")
            return None

    def get_buildings(self, object_type: str = "Building", page_size: int = 10000):
        """
        Haal een lijst van gebouwen op uit de API.

        Args:
            object_type (str): Type object om op te halen, standaard 'Building'.
            page_size (int): Aantal records per pagina, standaard 10.000.

        Returns:
            list of dict: De opgehaalde gebouwen als lijst met dictionaries
                          als succesvol, anders None.
        """
        try:
            logger.debug(f"Start get_buildings-aanvraag voor object_type={object_type}")

            # Controleer of er al een token is, anders authenticeren
            if not self.access_token:
                logger.debug("Geen access_token aanwezig, probeer te authenticeren")
                if not self.authenticate():
                    logger.error("Authenticatie mislukt tijdens get_buildings")
                    return None

            # Stel request voor om data op te halen
            url = f"{self.api_url}/v1/objects/filterByObjectType"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            params = {
                "objectType": object_type,
                "pageSize": page_size
            }

            # Log de details van het verzoek
            logger.debug(f"GET URL: {url}")
            logger.debug(f"Request headers: {headers}")
            logger.debug(f"Request parameters: {params}")

            # Verstuur de aanvraag
            logger.debug("Verstuur GET verzoek...")
            response = requests.get(url, headers=headers, params=params)

            # Log de response status en eventuele metadata
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")

            # Verwerk de response
            if response.status_code == 200:
                data = response.json()
                count = len(data) if isinstance(data, list) else "onbekend"
                logger.info(f"Succesvol {count} {object_type}(s) opgehaald.")
                if isinstance(data, list) and data:
                    logger.debug("Eerste paar records: " + str(data[:2]))
                else:
                    logger.debug("Geen records gevonden.")
                return data
            else:
                logger.error(f"Fout bij ophalen van gebouwen: {response.status_code}")
                logger.error(f"Foutmelding: {response.text}")
                logger.debug(f"Volledige response: {vars(response)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request fout in get_buildings: {str(e)}")
            logger.exception("Volledige stacktrace:")
            return None
        except Exception as e:
            logger.error(f"Onverwachte fout in get_buildings: {str(e)}")
            logger.exception("Volledige stacktrace:")
            return None

    def update_buildings(self, buildings_data):
        """
        Update gebouw-gegevens in de LUXS ACCEPT API.

        Args:
            buildings_data (list): Lijst met gebouw-objecten (dictionaries)
                                   om te updaten.

        Returns:
            bool: True als update succesvol, anders False.
        """
        logger.debug(f"Start update_buildings-aanvraag voor {len(buildings_data)} gebouwen")
        # Controleer of we een geldig token hebben
        if not self.access_token:
            self.authenticate()

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        update_url = f"{self.api_url}/v1/objects"
        logger.debug(f"PUT URL: {update_url}")
        # logger.debug(f"Request headers: {headers}")
        logger.debug(f"Request data: {buildings_data}")
        response = requests.put(update_url, json=buildings_data, headers=headers)
        if response.status_code == 200:
            logger.info(f"Succesvol {len(buildings_data)} gebouwen geüpdatet.")
            return True
        else:
            logger.error(f"Update gebouwen mislukt: {response.status_code} - {response.text}")
            return False

    def _validate_urls(self):
        """
        Controleer of de API en Auth URLs correct geformatteerd zijn en HTTPS gebruiken.

        Returns:
            bool: True als URL's geldig zijn, anders False.
        """
        try:
            # Parse de URLs
            api_parsed = urlparse(self.api_url)
            auth_parsed = urlparse(self.auth_url)

            # Controleer of HTTPS wordt gebruikt
            if api_parsed.scheme != "https":
                logger.error(f"API URL moet HTTPS gebruiken. Huidige scheme: {api_parsed.scheme}")
                return False

            if auth_parsed.scheme != "https":
                logger.error(f"Auth URL moet HTTPS gebruiken. Huidige scheme: {auth_parsed.scheme}")
                return False

            # Verwijder eventuele trailing slashes
            self.api_url = self.api_url.rstrip("/")

            return True
        except Exception as e:
            logger.error(f"URL validatie mislukt: {str(e)}")
            return False

def get_api_client():
    """
    Hulpfunctie om snel een LuxsAcceptClient instantie te krijgen.

    Returns:
        LuxsAcceptClient: Een instance van de LuxsAcceptClient.
    """
    return LuxsClient()
