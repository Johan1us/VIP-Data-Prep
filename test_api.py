import requests
import json
from dotenv import load_dotenv
import os
import logging
import time
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LuxsAcceptClient:
    def __init__(self):
        load_dotenv()
        self.auth_url = os.environ.get('LUXS_ACCEPT_AUTH_URL')
        self.api_url = os.environ.get('LUXS_ACCEPT_API_URL')
        self.client_id = os.environ.get('LUXS_ACCEPT_CLIENT_ID')
        self.client_secret = os.environ.get('LUXS_ACCEPT_CLIENT_SECRET')
        self.access_token = None
        
        # Validate URLs
        if not self._validate_urls():
            raise ValueError("Invalid URLs in configuration")
        
        logger.debug(f"API URL: {self.api_url}")
        logger.debug(f"Auth URL: {self.auth_url}")
        logger.debug(f"Client ID exists: {'Yes' if self.client_id else 'No'}")

    def _validate_urls(self):
        """Validate that URLs are properly formatted and use HTTPS"""
        try:
            # Parse URLs
            api_parsed = urlparse(self.api_url)
            auth_parsed = urlparse(self.auth_url)
            
            # Check if URLs use HTTPS
            if api_parsed.scheme != 'https':
                logger.error(f"API URL must use HTTPS. Current scheme: {api_parsed.scheme}")
                return False
            if auth_parsed.scheme != 'https':
                logger.error(f"Auth URL must use HTTPS. Current scheme: {auth_parsed.scheme}")
                return False
                
            # Remove double slashes in path
            self.api_url = self.api_url.rstrip('/')
            
            return True
        except Exception as e:
            logger.error(f"URL validation failed: {str(e)}")
            return False

    def authenticate(self):
        logger.info("Attempting authentication...")
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        try:
            response = requests.post(self.auth_url, data=auth_data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            logger.info("Authentication successful")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def make_request(self, endpoint, method='GET', data=None, params=None):
        """
        Make a request to the API
        
        Args:
            endpoint (str): API endpoint
            method (str): HTTP method (GET, POST, PUT)
            data (dict): Data to send in request body
            params (dict): Query parameters for GET requests
        """
        if not self.access_token:
            self.authenticate()

        url = f"{self.api_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method in ['POST', 'PUT']:
                response = requests.request(method, url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

def test_api():
    # Initialize client
    logger.info("Initializing API client...")
    api_client = LuxsAcceptClient()

    # First do a GET request to see current state
    logger.info("\n=== Testing GET request ===")
    try:
        response = api_client.make_request(
            'v1/objects/filterByObjectType',
            method='GET',
            params={
                'objectType': 'Building',
                'identifier': '10000',
                'onlyActive': 'false'
            }
        )
        if response.status_code == 200:
            logger.info("Current object state:")
            logger.info(json.dumps(response.json(), indent=2))
        else:
            logger.error(f"❌ GET request failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"❌ GET request failed with error: {str(e)}")

    # Test payloads - met alle huidige waarden
    test_payloads = [
        {
            "objectType": "Building",
            "identifier": "10000",
            "attributes": {
                "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam": "Jack Robbemond",
                "Description": "10000 - VvE Kolk",
                "Plaats": "ROTTERDAM",
                "Clustercode": "10000",
                "Clusternaam - IFC": "VvE Kolk"
            }
        }
    ]

    # Test POST requests
    logger.info(f"\n=== Testing POST requests ===")
    
    for i, payload in enumerate(test_payloads, 1):
        logger.info(f"\n--- POST Test {i} ---")
        try:
            response = api_client.make_request(
                'v1/objects',
                method='POST',
                data=[payload]
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data[0]['success']:
                    logger.info(f"✅ POST Test {i} Success!")
                else:
                    logger.warning(f"⚠️ POST Test {i} API Error: {response_data[0]['message']}")
                logger.info(f"Response: {json.dumps(response_data, indent=2)}")
            else:
                logger.error(f"❌ POST Test {i} HTTP Error {response.status_code}")
                logger.error(f"Response: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ POST Test {i} Exception: {str(e)}")
        
        time.sleep(1)

    # Do another GET to verify
    logger.info("\n=== Testing GET after POST ===")
    try:
        response = api_client.make_request(
            'v1/objects/filterByObjectType',
            method='GET',
            params={
                'objectType': 'Building',
                'identifier': '10000',
                'onlyActive': 'false'
            }
        )
        if response.status_code == 200:
            logger.info("Updated object state:")
            logger.info(json.dumps(response.json(), indent=2))
        else:
            logger.error(f"❌ GET request failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"❌ GET request failed with error: {str(e)}")

if __name__ == "__main__":
    test_api() 