import io
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ExcelHandler:
    def __init__(self, metadata):
        self.metadata = metadata

    def create_excel_file(self, data: list) -> io.BytesIO:
        # Maak een pandas DataFrame van data en schrijf naar Excel
        logger.debug("Exporteren van data naar Excel...")
        logger.debug(f"Eerste paar records: {data[:2]}")
        logger.debug(f"Converteer naar DataFrame...")
        df = pd.DataFrame(data)
        logger.debug(f"Kolommen: {df.columns}")
        logger.debug(f"Eerste paar records: {df.head(2)}")
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output
