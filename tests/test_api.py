from src.api_client import LuxsAcceptClient

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