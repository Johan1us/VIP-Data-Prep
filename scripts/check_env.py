from dotenv import load_dotenv
import os

load_dotenv()

# Extract environment variables
luxs_client_id = os.environ.get('LUXS_ACCEPT_CLIENT_ID')
luxs_client_secret = os.environ.get('LUXS_ACCEPT_CLIENT_SECRET')
luxs_api_url = os.environ.get('LUXS_ACCEPT_API_URL')
luxs_auth_url = os.environ.get('LUXS_ACCEPT_AUTH_URL')

# Print them for debugging (with partial masking for secrets)
def mask_secret(value, show_chars=4):
    if not value:
        return "Not set"
    return value[:show_chars] + '*' * (len(value) - show_chars)

print("\n=== LUXS Environment Variables ===")
print(f"API URL: {luxs_api_url}")
print(f"Auth URL: {luxs_auth_url}")
print(f"Client ID: {mask_secret(luxs_client_id)}")
print(f"Client Secret: {mask_secret(luxs_client_secret)}")
print("================================\n")

# Verify all required variables are set
required_vars = {
    'Client ID': luxs_client_id,
    'Client Secret': luxs_client_secret,
    'API URL': luxs_api_url,
    'Auth URL': luxs_auth_url
}

missing_vars = [name for name, value in required_vars.items() if not value]

if missing_vars:
    print("⚠️ Missing environment variables:")
    for var in missing_vars:
        print(f"- {var}")
else:
    print("✅ All environment variables are set!")


if __name__ == "__main__":
    pass
