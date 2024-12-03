import logging
from urllib.parse import urlparse

import requests

from .config import Config
from .utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


class LuxsAcceptClient:
    def __init__(self):
        # Load configuration
        config = Config.load_config()

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

    def authenticate(self):
        """Authenticate with the API using OAuth2 client credentials flow"""
        logger.info("Attempting authentication...")
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            response = requests.post(self.auth_url, data=auth_data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            logger.info("Authentication successful")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def make_request(self, endpoint, method="GET", data=None, params=None):
        """
        Make a request to the API

        Args:
            endpoint (str): API endpoint
            method (str): HTTP method (GET, POST, PUT)
            data (dict): Data to send in request body
            params (dict): Query parameters for GET requests
        """
        if not self.access_token:
            if not self.authenticate():
                raise Exception("Authentication failed")

        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method in ["POST", "PUT"]:
                response = requests.request(method, url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
