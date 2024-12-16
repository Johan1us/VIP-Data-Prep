import io
import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd
from xlsxwriter.workbook import Workbook
from io import BytesIO

logger = logging.getLogger(__name__)

def sanitize_name(name: str) -> str:
    cleaned = re.sub(r'[^A-Za-z0-9]', '_', name)
    if re.match(r'^[0-9_]', cleaned):
        cleaned = 'N' + cleaned
    return cleaned[:255]

def set_column_widths(worksheet, df: pd.DataFrame, min_width: int = 8, max_width: int = 50) -> None:
    """
    Set the column widths based on content and header length.

    Args:
        worksheet: The Excel worksheet object
        df: The DataFrame containing the data
        min_width: Minimum column width (default: 8)
        max_width: Maximum column width (default: 50)
    """
    for i, col in enumerate(df.columns):
        # Get maximum length from column header
        header_length = len(str(col))

        # Get maximum length from column content
        content_length = df[col].astype(str).map(len).max()
        content_length = content_length if not pd.isnull(content_length) else 0

        # Calculate optimal width (header length or content length + padding)
        optimal_width = max(header_length, content_length) + 2

        # Apply min/max constraints
        column_width = max(min_width, min(optimal_width, max_width))

        # Set the column width
        worksheet.set_column(i, i, column_width)

class ExcelHandler:
    def __init__(self,
                 metadata: Dict[str, Any],
                 columns_mapping: Dict[str, str],
                 object_type: str):
        """
        metadata: {internal_key: {...}}
        columns_mapping: {excelColumnName: internalAttributeName}
        """
        logger.debug("Initialiseren van ExcelHandler...")
        self.metadata = metadata
        self.columns_mapping = columns_mapping
        self.inverse_mapping = {v: k for k, v in columns_mapping.items()}
        self.object_type = object_type
        self.skip_identifier_insert = False

        # Required columns, met objectType en identifier vooraan
        self.required_columns = ["objectType", "identifier"] + list(columns_mapping.values())
        logger.debug("ExcelHandler geïnitialiseerd.")

    def create_excel_file(self, data: List[Dict[str, Any]], output: Optional[io.BytesIO] = None) -> io.BytesIO:
        if not data:
            raise ValueError("Geen data om te exporteren")

        if output is None:
            output = io.BytesIO()

        # Debug prints voor data structuur
        print(f"Data: {len(data)}")
        print(f"Type data: {type(data)}")
        print(f"Eerste object: {data[0] if data else 'Geen data'}")

        # Maak een DataFrame van de data
        df = pd.DataFrame(data)

        # Zorg ervoor dat we de identifier behouden als die in de originele data zit
        original_identifier = None
        if 'identifier' in df.columns:
            original_identifier = df['identifier'].copy()

        # attributes uitklappen eerst
        if 'attributes' in df.columns:
            df_attr = df['attributes'].apply(pd.Series)
            df = df.drop(columns=['attributes']).join(df_attr)

        # Voeg objectType toe indien niet aanwezig
        if 'objectType' not in df.columns:
            df.insert(0, 'objectType', self.object_type)
        else:
            df['objectType'] = self.object_type

        # Herstel de originele identifier of maak een nieuwe aan
        if original_identifier is not None:
            df['identifier'] = original_identifier
        elif 'identifier' not in df.columns:
            df.insert(1, 'identifier', [None] * len(df))

        # Booleans naar Ja/Nee
        boolean_keys = [k for k, v in self.metadata.items() if v.get('type') == 'BOOLEAN']
        for key in boolean_keys:
            if key in df.columns:
                df[key] = df[key].map({'true': 'Ja', 'false': 'Nee'}, na_action='ignore')

        # Zorg dat alle required_columns bestaan
        for rc in self.required_columns:
            if rc not in df.columns:
                df[rc] = None

        # Verwijder dubbele kolommen
        df = df.loc[:, ~df.columns.duplicated()]

        # Zorg ervoor dat de kolommen in de juiste volgorde staan
        columns_to_use = [col for col in self.required_columns if col in df.columns]
        df = df[columns_to_use]

        # Hernoem interne keys naar externe kolomnamen
        rename_map = {}
        for c in df.columns:
            if c in ["objectType", "identifier"]:
                continue
            excel_col = self.inverse_mapping.get(c)
            if excel_col:
                rename_map[c] = excel_col

        df.rename(columns=rename_map, inplace=True)

        # Debug print voor finale kolommen
        print(f"Finale kolommen in DataFrame: {df.columns.tolist()}")
        print(f"Eerste rij van finale data: {df.iloc[0].to_dict() if len(df) > 0 else 'Geen data'}")

        writer = pd.ExcelWriter(output, engine="xlsxwriter")
        df.to_excel(writer, index=False, sheet_name="Data")

        # Format the Excel sheet
        self.format_excel_sheet(writer.book, writer.sheets["Data"], df, self.metadata, self.columns_mapping)

        writer.close()
        output.seek(0)
        return output

    def format_excel_sheet(self, workbook: Workbook, worksheet, df: pd.DataFrame,
                          metadata: Dict[str, Any], columns_mapping: Dict[str, str]) -> None:
        """
        Format and style an Excel worksheet with proper headers, validation, and conditional formatting.

        Args:
            workbook: The Excel workbook object
            worksheet: The worksheet to format
            df: The DataFrame containing the data
            metadata: Dictionary containing field metadata
            columns_mapping: Mapping between Excel column names and internal names
        """
        # Create header format
        header_format = workbook.add_format({
            'bg_color': '#ededed',
            'align': 'left',
            'border': 1
        })

        # Format headers
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_format)

        # Set column widths using the new function
        set_column_widths(worksheet, df)

        # Add autofilter and freeze panes
        worksheet.autofilter(0, 0, 0, len(df.columns) - 1)
        worksheet.freeze_panes(1, 2)

        # Create lookup sheet for enumerations and boolean values
        lookup_sheet = workbook.add_worksheet("Lookup_Lists")

        # Add boolean options
        boolean_options = ["Ja", "Nee"]
        for i, opt in enumerate(boolean_options):
            lookup_sheet.write(i, 0, opt)
        workbook.define_name("BooleanList", f"='Lookup_Lists'!$A$1:$A$2")

        # Create inverse mapping
        inv_map = {ec: ic for ec, ic in columns_mapping.items()}

        # Handle enumerations
        enum_col = 1
        enum_ranges = {}
        created_named_ranges = set()

        for col_num, excel_col_name in enumerate(df.columns):
            if excel_col_name in ["objectType", "identifier"]:
                continue
            internal_key = inv_map[excel_col_name]
            field_meta = metadata.get(internal_key, {})

            if 'attributeValueOptions' in field_meta:
                options = field_meta['attributeValueOptions']
                list_name = sanitize_name(internal_key)
                if list_name not in created_named_ranges:
                    for row_i, val in enumerate(options):
                        lookup_sheet.write(row_i, enum_col, val)
                    col_letter = chr(ord('A') + enum_col)
                    workbook.define_name(list_name,
                                       f"='Lookup_Lists'!${col_letter}$1:${col_letter}${len(options)}")
                    enum_ranges[internal_key] = list_name
                    enum_col += 1
                    created_named_ranges.add(list_name)

        # Add data validation
        start_row = 1
        end_row = start_row + len(df) - 1

        # Lock first two columns
        for c in range(min(2, df.shape[1])):
            worksheet.data_validation(
                start_row, c, end_row, c,
                {
                    'validate': 'any',
                    'input_title': 'Let op!',
                    'input_message': 'Deze kolom mag niet worden aangepast.',
                    'show_input': True
                }
            )

        # Add field-specific validation
        for col_num, excel_col_name in enumerate(df.columns):
            if excel_col_name in ["objectType", "identifier"]:
                continue
            internal_key = inv_map[excel_col_name]
            field_meta = metadata.get(internal_key, {})

            # Boolean validation
            if field_meta.get('type') == 'BOOLEAN':
                worksheet.data_validation(start_row, col_num, end_row, col_num, {
                    "validate": "list",
                    "source": "=BooleanList"
                })

            # Enumeration validation
            if internal_key in enum_ranges:
                worksheet.data_validation(start_row, col_num, end_row, col_num, {
                    "validate": "list",
                    "source": f"={enum_ranges[internal_key]}"
                })

            # Date validation
            if field_meta.get('type') == 'DATE' and field_meta.get('dateFormat') == 'yyyy':
                worksheet.data_validation(start_row, col_num, end_row, col_num, {
                    'validate': 'integer',
                    'criteria': 'between',
                    'minimum': 1900,
                    'maximum': 2100,
                    'error_message': 'Geef een geldig jaar (1900-2100) op.'
                })

        # Add conditional formatting for boolean fields
        worksheet.conditional_format(start_row, 0, end_row, len(df.columns)-1, {
            'type': 'formula',
            'criteria': '=AND(INDIRECT("R"&ROW()&"C"&COLUMN(),FALSE)<>"Ja",INDIRECT("R"&ROW()&"C"&COLUMN(),FALSE)<>"Nee")',
            'format': workbook.add_format({'bg_color': '#FFFF00'})
        })

def create_excel_download(data: bytes) -> BytesIO:
    """Creëer een Excel bestand voor download"""
    try:
        # Converteer de bytes naar een BytesIO object
        excel_buffer = BytesIO(data)
        return excel_buffer
    except Exception as e:
        print(f"Error creating excel download: {e}")
        return None
