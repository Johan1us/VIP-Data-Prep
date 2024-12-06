import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import io

logger = logging.getLogger(__name__)

class BasePOService:
    def __init__(self, api_client, excel_handler, metadata: Dict[str, Any], columns_mapping: Dict[str, str]):
        """
        api_client: een instance van de APIClient
        excel_handler: ExcelHandler instance
        metadata: dict met metadata voor de dataset (attributen, types, opties)
        columns_mapping: dict met mapping van Excel kolomnamen naar interne attributen keys
        """
        self.api_client = api_client
        self.excel_handler = excel_handler
        self.metadata = metadata
        self.columns_mapping = columns_mapping

    def get_all_buildings(self) -> Optional[List[Dict[str, Any]]]:
        logger.info("Ophalen van alle buildings...")
        buildings = self.api_client.get_buildings(object_type="Building", page_size=10000)
        if buildings is not None:
            logger.info(f"{len(buildings)} gebouwen opgehaald.")
        return buildings

    def export_to_excel(self, data: List[Dict[str, Any]]) -> io.BytesIO:
        return self.excel_handler.create_excel_file(data)

    def process_uploaded_data(self, df: pd.DataFrame) -> bool:
        logger.info("Verwerken van geüploade gegevens...")

        # Valideer data
        self._validate_data(df)

        # Omzetten DataFrame -> updates
        update_data = []
        for _, row in df.iterrows():
            building_update = self._row_to_update_object(row)
            update_data.append(building_update)

        return self.update_buildings_in_batches(update_data)

    def _validate_data(self, df: pd.DataFrame) -> None:
        df = df.where(pd.notnull(df), None)

        # Valideer op basis van metadata
        for column, attribute_key in self.columns_mapping.items():
            if attribute_key == 'identifier':
                continue  # identifier wordt vaak niet gevalideerd

            attr_meta = self.metadata.get(attribute_key)
            if not attr_meta:
                # Als er geen metadata is voor deze kolom, sla over (of gooi error)
                continue

            col_values = df[column].dropna().unique()
            # Typechecks en option checks
            # Als er attributeValueOptions zijn, controleer of alle values daarin zitten
            if 'attributeValueOptions' in attr_meta:
                valid_options = attr_meta['attributeValueOptions']
                invalid = [v for v in col_values if v not in valid_options]
                if invalid:
                    raise ValueError(f"Ongeldige waarden voor {column}: {invalid}, "
                                     f"verwacht: {valid_options}")

            # Boolean checks
            if attr_meta['type'] == 'BOOLEAN':
                valid_bools = [True, False, "TRUE", "FALSE", "Ja", "Nee", 1, 0, None]
                invalid_bools = [v for v in col_values if v not in valid_bools]
                if invalid_bools:
                    raise ValueError(f"Ongeldige boolean waarden in {column}: {invalid_bools}. "
                                     f"Geldige waarden: {valid_bools}")

    def _row_to_update_object(self, row: pd.Series) -> Dict[str, Any]:
        # Hier converteren we elke kolom naar het juiste formaat op basis van metadata
        attributes = {}
        for col_name, attr_key in self.columns_mapping.items():
            if attr_key == 'identifier':
                continue
            attr_meta = self.metadata.get(attr_key)
            value = row[col_name]

            # Converteer waarde op basis van type
            converted_value = self._convert_value(value, attr_meta)

            attributes[attr_meta['name']] = converted_value

        return {
            "objectType": "Building",
            "identifier": str(row[self._get_identifier_column()]),
            "attributes": attributes
        }

    def _get_identifier_column(self) -> str:
        # Zoek de kolomnaam uit columns_mapping die 'identifier' mapped
        for col, key in self.columns_mapping.items():
            if key == 'identifier':
                return col
        raise ValueError("Geen identifier kolom gedefinieerd in columns_mapping.")

    def _convert_value(self, value, attr_meta):
        if value is None:
            return None

        attr_type = attr_meta['type']

        if attr_type == 'BOOLEAN':
            return self._to_boolean(value)
        elif attr_type == 'STRING':
            # Speciale logica voor jaar bijvoorbeeld:
            if 'jaar_laatste_dakonderhoud' in attr_meta['name'].lower():
                return self._convert_jaar_onderhoud(value)
            else:
                return str(value)
        # Voeg hier indien nodig meer typeconversies toe
        return value

    def _to_boolean(self, value) -> str:
        val_str = str(value).lower()
        if val_str in ['true', '1', 'yes', 'ja']:
            return "true"
        return "false"

    def _convert_jaar_onderhoud(self, value):
        # Probeer jaartal te bepalen:
        try:
            if isinstance(value, str) and 'T' in value:
                return str(pd.to_datetime(value).year)
            else:
                return str(int(float(value)))
        except:
            return None

    def update_buildings_in_batches(self, buildings_data: List[Dict[str, Any]], batch_size: int = 100, max_retries: int = 3) -> bool:
        total_buildings = len(buildings_data)
        logger.info(f"Updaten van {total_buildings} buildings in batches...")

        for i in range(0, total_buildings, batch_size):
            batch = buildings_data[i:i+batch_size]
            success = False
            attempts = 0
            batch_number = (i // batch_size) + 1

            while not success and attempts < max_retries:
                attempts += 1
                try:
                    api_success = self.api_client.update_buildings(batch)
                    if api_success:
                        success = True
                        logger.info(f"Batch {batch_number} succesvol bijgewerkt bij poging {attempts}.")
                    else:
                        logger.error(f"Batch {batch_number} mislukt bij poging {attempts}")
                except Exception as e:
                    logger.error(f"Fout bij batch {batch_number}, poging {attempts}: {e}")

            if not success:
                logger.error(f"Niet gelukt om batch {batch_number} te updaten na {max_retries} pogingen.")
                return False
        logger.info("Alle batches succesvol bijgewerkt.")
        return True
