import os
import requests
from dotenv import load_dotenv

def check_auth():
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    client_id = os.environ.get('LUXS_ACCEPT_CLIENT_ID')
    client_secret = os.environ.get('LUXS_ACCEPT_CLIENT_SECRET')
    auth_url = os.environ.get('LUXS_ACCEPT_AUTH_URL')
    
    # Verify all required variables are present
    if not all([client_id, client_secret, auth_url]):
        print("❌ Missing required environment variables!")
        return False
    
    try:
        # Prepare the request for OAuth2 client credentials flow
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        print("🔄 Attempting authentication...")
        
        # Make the authentication request
        response = requests.post(auth_url, data=auth_data)
        
        # Check if request was successful
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Authentication successful!")
            print(f"Token type: {token_data.get('token_type', 'N/A')}")
            print(f"Expires in: {token_data.get('expires_in', 'N/A')} seconds")
            return True
        else:
            print(f"❌ Authentication failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n=== LUXS Accept API Authentication Check ===")
    success = check_auth()
    print("==========================================\n")
    
    # Exit with appropriate status code
    exit(0 if success else 1) 