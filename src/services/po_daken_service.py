import logging
import pandas as pd
from typing import List, Dict, Any, Optional
import requests
import io

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
        logger.info("Exporting data to Excel")
        if not data:
            logger.error("No data to export")
            raise ValueError("No data to export")

        try:
            # Create a BytesIO object to hold the Excel file
            output = io.BytesIO()

            # Create Excel writer with xlsxwriter engine
            writer = pd.ExcelWriter(output, engine="xlsxwriter")

            # Create DataFrame and process it
            df = pd.DataFrame(data)
            df = pd.concat(
                [df.drop(["attributes"], axis=1), df["attributes"].apply(pd.Series)],
                axis=1,
            )

            # Keep only the columns we need
            columns = [
                "objectType",
                "identifier",
                "Dakpartner - Building - Woonstad Rotterdam",
                "Jaar laatste dakonderhoud - Building - Woonstad Rotterdam",
                "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam",
                "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
                "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
            ]
            df = df[columns]

            # Write to Excel
            df.to_excel(writer, index=False, sheet_name="Data")

            # Add validation lists and data validation
            self._add_excel_validation(writer, df, columns)

            # Save and return the BytesIO object
            writer.close()
            output.seek(0)

            logger.info("Excel file generated successfully")
            return output

        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            raise

    def _add_excel_validation(self, writer, df, columns):
        """Add data validation to Excel file"""
        workbook = writer.book
        worksheet = writer.sheets["Data"]
        lookup_sheet = workbook.add_worksheet("Lookup_Lists")

        # Add validation lists
        self._add_validation_lists(workbook, lookup_sheet)

        # Add column validation
        start_row = 1
        end_row = len(df) + 1

        # Add validation for specific columns
        self._add_column_validation(worksheet, columns, start_row, end_row)

    def _add_validation_lists(self, workbook, lookup_sheet):
        """Add validation lists to lookup sheet"""
        # Dakpartner options
        dakpartner_options = self.METADATA["dakpartner"]["attributeValueOptions"]
        for row_num, option in enumerate(dakpartner_options):
            lookup_sheet.write(row_num, 0, option)
        dakpartner_list_range = f"'Lookup_Lists'!$A$1:$A${len(dakpartner_options)}"
        workbook.define_name("DakpartnerList", f"={dakpartner_list_range}")

        # Projectleider options
        projectleider_options = self.METADATA["projectleider"]["attributeValueOptions"]
        for row_num, option in enumerate(projectleider_options):
            lookup_sheet.write(row_num, 1, option)
        projectleider_list_range = f"'Lookup_Lists'!$B$1:$B${len(projectleider_options)}"
        workbook.define_name("ProjectleiderList", f"={projectleider_list_range}")

        # Boolean options
        boolean_options = ["TRUE", "FALSE"]
        for row_num, option in enumerate(boolean_options):
            lookup_sheet.write(row_num, 2, option)
        boolean_list_range = f"'Lookup_Lists'!$C$1:$C${len(boolean_options)}"
        workbook.define_name("BooleanList", f"={boolean_list_range}")

    def _add_column_validation(self, worksheet, columns, start_row, end_row):
        """Add data validation to specific columns"""
        # Dakpartner validation
        dakpartner_col = columns.index("Dakpartner - Building - Woonstad Rotterdam")
        worksheet.data_validation(
            start_row,
            dakpartner_col,
            end_row,
            dakpartner_col,
            {"validate": "list", "source": "=DakpartnerList"},
        )

        # Projectleider validation
        projectleider_col = columns.index(
            "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"
        )
        worksheet.data_validation(
            start_row,
            projectleider_col,
            end_row,
            projectleider_col,
            {"validate": "list", "source": "=ProjectleiderList"},
        )

        # Boolean validations
        boolean_columns = [
            "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
            "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
        ]
        for col_name in boolean_columns:
            if col_name in columns:
                col_index = columns.index(col_name)
                worksheet.data_validation(
                    start_row,
                    col_index,
                    end_row,
                    col_index,
                    {"validate": "list", "source": "=BooleanList"},
                )

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
