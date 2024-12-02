import os
from dotenv import load_dotenv
import requests
import json

# Load environment variables from .env file
load_dotenv()

TOKEN_URL = "https://auth.accept.luxsinsights.com/oauth2/token"

# Get credentials from environment variables
CLIENT_ID = os.environ.get('LUXS_ACCEPT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('LUXS_ACCEPT_CLIENT_SECRET')

# print(CLIENT_ID)
# print(CLIENT_SECRET)
# Get bearer token
def get_token():
    if not all([CLIENT_ID, CLIENT_SECRET]):
        print("❌ Missing required environment variables!")
        return False

    try:
        # Prepare the request for OAuth2 client credentials flow
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        print("🔄 Attempting authentication...")

        # Make the authentication request
        response = requests.post(TOKEN_URL, data=auth_data)

        # Check if request was successful
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Authentication successful!")
            print(f"Token type: {token_data.get('token_type', 'N/A')}")
            print(f"Expires in: {token_data.get('expires_in', 'N/A')} seconds")
            TOKEN = token_data.get('access_token')
            return TOKEN
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

def get_metadata(object_type, token=None):
    """
    Fetches metadata for specified object type from the LUXS Accept API.
    
    Args:
        object_type (str): The type of object to fetch metadata for (e.g., 'Aanrecht')
        token (str, optional): Existing bearer token. If None, will fetch new token.
        
    Returns:
        dict: Metadata if successful, False otherwise
    """
    METADATA_URL = "https://api.accept.luxsinsights.com/v1/metadata"
    
    try:
        # Use provided token or get new one
        TOKEN = token if token else get_token()
        if not TOKEN:
            return False

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        }

        # Prepare request parameters
        params = {
            'objectType': object_type
        }

        print(f"\n🔄 Fetching metadata for {object_type}...")
        
        response = requests.get(METADATA_URL, headers=headers, params=params)

        # Check if request was successful
        if response.status_code == 200:
            metadata = response.json()
            print("✅ Metadata retrieved successfully!")
            # Pretty print the JSON with indentation
            print("\nMetadata:")
            print(json.dumps(metadata, indent=2))
            return metadata
        else:
            print(f"❌ Metadata request failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

# https://api.accept.luxsinsights.com/v1/objects/filterByObjectType?objectType=Unit&identifier=10000000025
def get_object_by_filter(object_type, attributes_filter, identifier, token=None):
    """
    Fetches objects of specified type filtered by attributes from the LUXS Accept API.

    Args:
        object_type (str): The type of object to fetch (e.g., 'Space')
        attributes_filter (dict): Filter attributes (e.g., {'ComplexId': '11000'})
        identifier (str): Identifier of the object to fetch
        token (str, optional): Existing bearer token. If None, will fetch new token.

    Returns:
        dict: Object data if successful, False otherwise
    """
    FILTER_URL = "https://api.accept.luxsinsights.com/v1/objects/filterByObjectType"

    try:
        # Use provided token or get new one
        TOKEN = token if token else get_token()
        if not TOKEN:
            return False

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        }

        # Prepare request parameters
        params = {
            'objectType': object_type,
            'identifier': identifier
        }

        print(f"\n🔄 Fetching {object_type} object with filter...")
        print("\nFilter attributes:")
        print(json.dumps(attributes_filter, indent=2))

        response = requests.get(FILTER_URL, headers=headers, params=params)

        # Check if request was successful
        if response.status_code == 200:
            object_data = response.json()
            print("✅ Object retrieved successfully!")
            # Pretty print the JSON with indentation
            print("\nObject data:")
            print(json.dumps(object_data, indent=2))
            return object_data
        else:
            print(f"❌ Object retrieval failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


# POST request to create a new object
def create_object(object_type, data, token=None):
    """
    Creates a new object of specified type using the LUXS Accept API.
    """
    CREATE_URL = "https://api.accept.luxsinsights.com/v1/objects"

    try:
        TOKEN = token if token else get_token()
        if not TOKEN:
            return False

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }

        print(f"\n🔄 Creating new {object_type} object...")
        print("\nRequest data:")
        print(json.dumps(data, indent=2))  # Print the request data

        response = requests.post(CREATE_URL, headers=headers, json=data)

        if response.status_code == 200:
            response_data = response.json()
            print("✅ Object created successfully!")
            print("\nResponse:")
            print(json.dumps(response_data, indent=2))
            return response_data
        else:
            print(f"❌ Object creation failed with status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Error: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def update_toilet_floor(unit_id, new_value="Hout", token=None):
    """
    Updates the floor material attribute for a toilet unit.
    
    Args:
        unit_id (str): The identifier of the Unit object
        new_value (str): The new floor material value (default: "Hout")
        token (str, optional): Authentication token
    
    Returns:
        dict: Response data if successful, False otherwise
    """
    # Validate the new_value against allowed options
    VALID_VALUES = ["Beton", "Hout", "Lewisplaat"]
    if new_value not in VALID_VALUES:
        print(f"❌ '{new_value}' is an invalid value. Must be one of: {', '.join(VALID_VALUES)}")
        return False

    update_data = [{
        "objectType": "Unit",
        "identifier": unit_id,
        "parentObjectType": "Building",
        "parentIdentifier": "11000",
        "attributes": {
            "Opbouw + materialisering vloer - Toilet 2e -  Woonstad Rotterdam": new_value
        }
    }]

    return create_object('Unit', update_data, token=token)

if __name__ == "__main__":
    print("\n=== LUXS Accept API Authentication Check ===")
    token = get_token()
    print("==========================================\n")

    if token:
        # Example usage of get_metadata
        # metadata = get_metadata('IfcUpload', token=token)

        # Example usage of update_toilet_floor
        # response = update_toilet_floor("10000000025", "beton", token=token)
        # print(f"\nResponse: {response}")

        # Example usage of get_object_by_filter
        object_data = get_object_by_filter('Unit', {"identifier": "10000000025"}, "10000000025", token=token)



        # Example data structure
        # sample_data = [
        #     {
        #         "objectType": "Space",
        #         "identifier": "Space_137680174",
        #         "parentObjectType": "Building",
        #         "parentIdentifier": "11000",  # Using ComplexId as parent identifier
        #         "attributes": {
        #             "Description": "Bastiaan test",
        #             "GUID - Woonstad Rotterdam": "XX2sCTcYeWH6YucKp_hkyqpk",
        #             "EenheidId - Woonstad Rotterdam": "11000000005",
        #             "ComplexId - Woonstad Rotterdam": "11000",
        #             "Uniek_ID": "Closetcombinatie_56844295X",
        #             "OGE Nummer": "11000000005",
        #             "ObjectType - Woonstad Rotterdam": "Closetcombinatie",
        #             "RuimterelatieId - Woonstad Rotterdam": "Space_137680174"
        #         }
        #     }
        # ]
        #
        # new_object = create_object('Space', sample_data, token=token)


