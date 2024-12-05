import logging
import pandas as pd
from typing import List, Dict, Any, Optional
import requests
import io
from utils.excel_utils import ExcelHandler

logger = logging.getLogger(__name__)

try:
    from .api import get_api_client
    logger.debug("Successfully imported get_api_client")
except ImportError as e:
    logger.error(f"Failed to import get_api_client: {str(e)}")
    raise ImportError("Required dependency 'get_api_client' not found. Please ensure the API module is properly installed.")

class PODakenService:
    """Service for handling PO Daken data operations"""

    # Using the same metadata as RoofManager
    METADATA = {
        "dakpartner": {
            "name": "Dakpartner - Building - Woonstad Rotterdam",
            "type": "STRING",
            "attributeValueOptions": [
                "Cazdak Dakbedekkingen BV",
                "Oranjedak West BV",
                "Voormolen Dakbedekkingen B.V.",
            ],
        },
        "projectleider": {
            "name": "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam",
            "type": "STRING",
            "attributeValueOptions": ["Jack Robbemond", "Anton Jansen"],
        },
        "dakveiligheid": {
            "name": "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
            "type": "BOOLEAN",
        },
        "antenne": {
            "name": "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
            "type": "BOOLEAN",
        },
    }

    def __init__(self):
        logger.info("Initializing PODakenService")
        try:
            self.api_client = get_api_client()
            logger.debug("Successfully initialized API client")
        except Exception as e:
            error_msg = f"Failed to initialize API client: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        self.excel_handler = ExcelHandler(self.METADATA)

    def get_all_buildings(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch all buildings with roof-related attributes"""
        logger.info("Starting to fetch all buildings...")

        BUILDINGS_URL = "https://api.accept.luxsinsights.com/v1/objects/filterByObjectType"

        try:
            token = self.api_client.authenticate()
            if not token:
                logger.error("Failed to authenticate")
                return None

            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {token}"
            }
            params = {"objectType": "Building", "pageSize": 10000}

            logger.debug(f"Sending GET request to {BUILDINGS_URL}")
            logger.debug(f"Request params: {params}")

            response = requests.get(BUILDINGS_URL, headers=headers, params=params)
            logger.debug(f"Received response with status code {response.status_code}")

            if response.status_code == 200:
                buildings = response.json()
                logger.info(f"Retrieved {len(buildings)} buildings")
                return buildings

            logger.error(f"Building retrieval failed with status code: {response.status_code}")
            logger.error(f"Error: {response.text}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def export_to_excel(self, data: List[Dict[str, Any]]) -> io.BytesIO:
        """Export building data to Excel and return as BytesIO object"""
        return self.excel_handler.create_excel_file(data)

    def process_uploaded_data(self, df: pd.DataFrame) -> bool:
        """Process and validate uploaded Excel data"""
        logger.info("Processing uploaded data")

        try:
            # Validate the dataframe structure and content
            self._validate_data(df)

            # Process each row and prepare update data
            update_data = []
            for _, row in df.iterrows():
                # Clean and validate the year value
                jaar_onderhoud = row["Jaar laatste dakonderhoud - Building - Woonstad Rotterdam"]
                if pd.isna(jaar_onderhoud) or pd.isnull(jaar_onderhoud):
                    jaar_onderhoud = ""
                else:
                    # Handle different date formats
                    try:
                        if isinstance(jaar_onderhoud, str) and 'T' in jaar_onderhoud:
                            # Parse ISO format date and extract year
                            jaar_onderhoud = str(pd.to_datetime(jaar_onderhoud).year)
                        else:
                            # Handle numeric years
                            jaar_onderhoud = str(int(float(jaar_onderhoud)))
                    except:
                        # If conversion fails, leave empty
                        jaar_onderhoud = ""

                # Clean boolean values
                dakveiligheid = str(row["Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam"]).lower()
                if pd.isna(dakveiligheid) or pd.isnull(dakveiligheid):
                    dakveiligheid = "false"
                elif dakveiligheid in ['true', '1', 'yes', 'ja']:
                    dakveiligheid = "true"
                else:
                    dakveiligheid = "false"

                antenne = str(row["Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam"]).lower()
                if pd.isna(antenne) or pd.isnull(antenne):
                    antenne = "false"
                elif antenne in ['true', '1', 'yes', 'ja']:
                    antenne = "true"
                else:
                    antenne = "false"

                building_update = {
                    "objectType": "Building",
                    "identifier": str(row["identifier"]),
                    "attributes": {
                        "Dakpartner - Building - Woonstad Rotterdam":
                            str(row["Dakpartner - Building - Woonstad Rotterdam"]) if not pd.isna(row["Dakpartner - Building - Woonstad Rotterdam"]) else "",
                        "Jaar laatste dakonderhoud - Building - Woonstad Rotterdam": jaar_onderhoud,
                        "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam":
                            str(row["Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"]) if not pd.isna(row["Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"]) else "",
                        "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam": dakveiligheid,
                        "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam": antenne
                    }
                }
                update_data.append(building_update)

            # Send update request
            return self.api_client.update_buildings(update_data)

        except Exception as e:
            logger.error(f"Error processing uploaded data: {str(e)}")
            raise

    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate the data types and values in the uploaded dataframe"""
        # Validate Dakpartner values
        valid_dakpartners = self.METADATA["dakpartner"]["attributeValueOptions"]
        invalid_dakpartners = df[df["Dakpartner - Building - Woonstad Rotterdam"].notna() &
                               ~df["Dakpartner - Building - Woonstad Rotterdam"].isin(valid_dakpartners)]
        if not invalid_dakpartners.empty:
            raise ValueError(f"Invalid Dakpartner values found: {invalid_dakpartners['Dakpartner - Building - Woonstad Rotterdam'].unique()}")

        # Validate Projectleider values
        valid_projectleiders = self.METADATA["projectleider"]["attributeValueOptions"]
        invalid_projectleiders = df[df["Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"].notna() &
                                  ~df["Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"].isin(valid_projectleiders)]
        if not invalid_projectleiders.empty:
            raise ValueError(f"Invalid Projectleider values found: {invalid_projectleiders['Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam'].unique()}")

        # Validate boolean fields
        boolean_columns = [
            "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
            "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam"
        ]
        for col in boolean_columns:
            invalid_bools = df[df[col].notna() & ~df[col].isin([True, False, "TRUE", "FALSE", "True", "False", 1, 0])]
            if not invalid_bools.empty:
                raise ValueError(f"Invalid boolean values found in {col}")
