from src.api_client import LuxsAcceptClient


def check_auth() -> bool:
    """Check authentication with LUXS API and return success status."""
    try:
        client = LuxsAcceptClient()
        if client.authenticate():
            print("✅ Authentication successful!")
            return True
        else:
            print("❌ Authentication failed!")
            return False
    except Exception as e:
        print(f"❌ Error during authentication: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n=== LUXS Accept API Authentication Check ===")
    success = check_auth()
    print("==========================================\n")
    exit(0 if success else 1)
