import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    # Required environment variables
    REQUIRED_VARS: Dict[str, str] = {
        "LUXS_ACCEPT_CLIENT_ID": "Client ID for API authentication",
        "LUXS_ACCEPT_CLIENT_SECRET": "Client secret for API authentication",
        "LUXS_ACCEPT_API_URL": "Base URL for the LUXS API",
        "LUXS_ACCEPT_AUTH_URL": "Authentication URL for the LUXS API",
    }

    @classmethod
    def load_config(cls) -> Dict[str, str]:
        """Load and validate environment configuration"""
        load_dotenv()

        config: Dict[str, str] = {}
        missing_vars = []

        logger.debug("Loading environment variables:")
        for var, description in cls.REQUIRED_VARS.items():
            value = os.environ.get(var)
            # Force HTTPS for API and Auth URLs
            if var in ["LUXS_ACCEPT_API_URL", "LUXS_ACCEPT_AUTH_URL"] and value:
                if value.startswith("http://"):
                    value = value.replace("http://", "https://")
                    logger.debug(f"Converted {var} to HTTPS")

            logger.debug(f"{var}: {cls.mask_secret(value) if value else 'Not set'}")
            if not value:
                missing_vars.append(f"{var} ({description})")
            config[var] = value

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables:\n"
                + "\n".join(f"- {var}" for var in missing_vars)
            )

        return config

    @staticmethod
    def mask_secret(value: Optional[str]) -> str:
        """Mask sensitive information in string values."""
        if not value:
            return "Not set"
        return value[:4] + "*" * (len(value) - 4)

    @classmethod
    def create_env_template(cls):
        """Create a template .env file"""
        env_content = "\n".join(
            f"{var}=your_{var.lower()}" for var in cls.REQUIRED_VARS.keys()
        )

        with open(".env.template", "w") as f:
            f.write(env_content)

        logger.info("Created .env.template file")
