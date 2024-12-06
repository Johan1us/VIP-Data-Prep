import io
import pandas as pd

class ExcelHandler:
    def __init__(self, metadata):
        self.metadata = metadata

    def create_excel_file(self, data: list) -> io.BytesIO:
        # Maak een pandas DataFrame van data en schrijf naar Excel
        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output
