import logging
import requests
from config_ import Config
from urllib.parse import urlparse
logger = logging.getLogger(__name__)

class LuxsAcceptClient:
    def __init__(self):
        logger.debug("Initializing APIClient")
        # Load configuration
        config = Config.load_config()
        logger.debug("Configuration loaded")

        # Debug log the actual URLs
        logger.debug("Loaded configuration:")
        logger.debug(f"API URL from config: {config['LUXS_ACCEPT_API_URL']}")
        logger.debug(f"Auth URL from config: {config['LUXS_ACCEPT_AUTH_URL']}")

        self.auth_url = config["LUXS_ACCEPT_AUTH_URL"]
        self.api_url = config["LUXS_ACCEPT_API_URL"]
        self.client_id = config["LUXS_ACCEPT_CLIENT_ID"]
        self.client_secret = config["LUXS_ACCEPT_CLIENT_SECRET"]
        self.access_token = None

        # Validate URLs
        if not self._validate_urls():
            raise ValueError("Invalid URLs in configuration")

        logger.debug(f"API URL: {self.api_url}")
        logger.debug(f"Auth URL: {self.auth_url}")
        logger.debug(f"Client ID exists: {'Yes' if self.client_id else 'No'}")

    def authenticate(self) -> str:
        """
        Authenticate with the LUXS API using OAuth2 client credentials flow.
        
        Returns:
            str: Access token if successful, None otherwise
        """
        try:
            # Prepare authentication data
            auth_data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            # Make authentication request to the correct endpoint
            auth_url = "https://auth.accept.luxsinsights.com/oauth2/token"
            response = requests.post(auth_url, data=auth_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                logger.info("Authentication successful")
                return self.access_token
            else:
                logger.error(f"Authentication failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def get_buildings(self, object_type: str = "Building", page_size: int = 10000):
        """
        Fetch buildings from the API.
        
        Args:
            object_type (str): Type of object to fetch (default: "Building")
            page_size (int): Number of records per page (default: 10000)
            
        Returns:
            List of buildings if successful, None otherwise
        """
        try:
            logger.debug(f"Starting get_buildings request for {object_type}")
            
            # Ensure we have a valid token
            if not self.access_token:
                logger.debug("No access token found, attempting authentication")
                if not self.authenticate():
                    logger.error("Authentication failed during get_buildings")
                    return None
            
            # Log request details
            url = f"{self.api_url}/v1/objects/filterByObjectType"
            logger.debug(f"Request URL: {url}")
            logger.debug(f"Page size: {page_size}")
            
            # Prepare request
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            params = {
                "objectType": object_type,
                "pageSize": page_size
            }
            
            logger.debug(f"Request headers: {headers}")
            logger.debug(f"Request parameters: {params}")

            # Make request
            logger.debug("Sending GET request...")
            response = requests.get(url, headers=headers, params=params)
            
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved {len(data) if isinstance(data, list) else 'unknown'} {object_type} objects")
                logger.debug("First few records:" + str(data[:2]) if isinstance(data, list) and data else "No records found")
                return data
            else:
                logger.error(f"Failed to retrieve buildings: {response.status_code}")
                logger.error(f"Error response: {response.text}")
                logger.debug(f"Full response object: {vars(response)}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception in get_buildings: {str(e)}")
            logger.exception("Full traceback:")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_buildings: {str(e)}")
            logger.exception("Full traceback:")
            return None

    def update_buildings(self, buildings_data):
        """
        Update buildings in the LUXS API
        
        Args:
            buildings_data: List of building data to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.access_token:
            self.authenticate()

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        update_url = f"{self.api_url}/v1/objects"
        response = requests.put(update_url, json=buildings_data, headers=headers)
        if response.status_code == 200:
            logger.info(f"Successfully updated {len(buildings_data)} buildings")
            return True
        else:
            logger.error(f"Buildings update mislukt: {response.status_code} - {response.text}")
            return False

    def _validate_urls(self):
        """Validate that URLs are properly formatted and use HTTPS"""
        try:
            # Parse URLs
            api_parsed = urlparse(self.api_url)
            auth_parsed = urlparse(self.auth_url)

            # Check if URLs use HTTPS
            if api_parsed.scheme != "https":
                logger.error(
                    f"API URL must use HTTPS. Current scheme: {api_parsed.scheme}"
                )
                return False
            if auth_parsed.scheme != "https":
                logger.error(
                    f"Auth URL must use HTTPS. Current scheme: {auth_parsed.scheme}"
                )
                return False

            # Remove double slashes in path
            self.api_url = self.api_url.rstrip("/")

            return True
        except Exception as e:
            logger.error(f"URL validation failed: {str(e)}")
            return False
        
def get_api_client():
    return LuxsAcceptClient()
