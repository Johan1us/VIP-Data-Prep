import os
import requests
from dotenv import load_dotenv

class LuxsAcceptClient:
    def __init__(self):
        load_dotenv()
        self.auth_url = os.environ.get('LUXS_ACCEPT_AUTH_URL')
        self.api_url = os.environ.get('LUXS_ACCEPT_API_URL')
        self.client_id = os.environ.get('LUXS_ACCEPT_CLIENT_ID')
        self.client_secret = os.environ.get('LUXS_ACCEPT_CLIENT_SECRET')
        self.access_token = None

    def authenticate(self):
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post(self.auth_url, data=auth_data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            return True
        return False

    def make_request(self, endpoint, method='GET', data=None):
        if not self.access_token:
            if not self.authenticate():
                raise Exception("Authentication failed")

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data
        )
        return response 