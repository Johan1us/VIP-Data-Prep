import os

def set_env_variables():
    # Define the environment variables
    env_vars = {
        'LUXS_ACCEPT_CLIENT_ID': 'your_client_id',
        'LUXS_ACCEPT_CLIENT_SECRET': 'your_client_secret',
        'LUXS_ACCEPT_API_URL': 'https://api.accept.luxsinsights.com/',
        'LUXS_ACCEPT_AUTH_URL': 'https://auth.accept.luxsinsights.com/oauth2/token'
    }

    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value

    # Print confirmation with masked secrets
    print("\n=== Setting LUXS Environment Variables ===")
    for key, value in env_vars.items():
        if 'SECRET' in key or 'ID' in key:
            # Mask sensitive data
            masked_value = value[:4] + '*' * (len(value) - 4)
            print(f"{key}: {masked_value}")
        else:
            print(f"{key}: {value}")
    print("=====================================\n")

if __name__ == "__main__":
    set_env_variables()