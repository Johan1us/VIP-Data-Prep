def create_env_file() -> None:
    """Create a .env file with default environment variables."""
    env_content = """LUXS_ACCEPT_CLIENT_ID=your_client_id
LUXS_ACCEPT_CLIENT_SECRET=your_client_secret
LUXS_ACCEPT_API_URL=https://api.accept.luxsinsights.com/
LUXS_ACCEPT_AUTH_URL=https://auth.accept.luxsinsights.com/oauth2/token
"""

    # Write to .env file
    with open("../.env", "w") as f:
        f.write(env_content)

    print("Created .env file with environment variables!")
    print("Remember to add .env to your .gitignore file")


if __name__ == "__main__":
    create_env_file()
