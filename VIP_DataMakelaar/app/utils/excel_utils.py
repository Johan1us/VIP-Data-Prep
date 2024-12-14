import io
import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd
from xlsxwriter.workbook import Workbook

logger = logging.getLogger(__name__)

def sanitize_name(name: str) -> str:
    cleaned = re.sub(r'[^A-Za-z0-9]', '_', name)
    if re.match(r'^[0-9_]', cleaned):
        cleaned = 'N' + cleaned
    return cleaned[:255]

class ExcelHandler:
    def __init__(self,
                 metadata: Dict[str, Any],
                 columns_mapping: Dict[str, str],
                 object_type: str = "Building"):
        """
        metadata: {internal_key: {...}}
        columns_mapping: {excelColumnName: internalAttributeName}
        """
        logger.debug("Initialiseren van ExcelHandler...")
        self.metadata = metadata
        self.columns_mapping = columns_mapping
        self.inverse_mapping = {v: k for k, v in columns_mapping.items()}
        self.object_type = object_type

        # Required columns, met objectType en identifier vooraan
        self.required_columns = ["objectType", "identifier"] + list(columns_mapping.values())
        logger.debug("ExcelHandler geïnitialiseerd.")

    def create_excel_file(self, data: List[Dict[str, Any]], output: Optional[io.BytesIO] = None) -> io.BytesIO:
        if not data:
            raise ValueError("Geen data om te exporteren")

        if output is None:
            output = io.BytesIO()

        df = pd.DataFrame(data)

        # Voeg objectType en identifier toe indien niet aanwezig
        if 'objectType' not in df.columns:
            df.insert(0, 'objectType', self.object_type)
        else:
            # Als objectType al bestaat, overschrijf dan de waarden:
            df['objectType'] = self.object_type

        if 'identifier' not in df.columns:
            # Als identifier niet in data staat, zet None of zorg dat data deze heeft.
            # Hier gaan we er vanuit dat hij wel bestaat. Als niet, dan:
            # df['identifier'] = None
            if 'identifier' not in df.columns:
                df['identifier'] = None
            df.insert(1, 'identifier', df['identifier'])

        # attributes uitklappen
        if 'attributes' in df.columns:
            df_attr = df['attributes'].apply(pd.Series)
            df = df.drop(columns=['attributes']).join(df_attr)

        # Booleans naar Ja/Nee
        boolean_keys = [k for k, v in self.metadata.items() if v.get('type') == 'BOOLEAN']
        for key in boolean_keys:
            if key in df.columns:
                df[key] = df[key].map({'true': 'Ja', 'false': 'Nee'}, na_action='ignore')

        # Zorg dat alle required_columns bestaan
        for rc in self.required_columns:
            if rc not in df.columns:
                df[rc] = None

        df = df[self.required_columns]

        # Hernoem interne keys naar externe kolomnamen
        # Skip objectType en identifier bij hernoemen (die staan niet in mapping)
        rename_map = {}
        for c in df.columns:
            if c in ["objectType", "identifier"]:
                continue
            excel_col = self.inverse_mapping.get(c)
            if excel_col:
                rename_map[c] = excel_col

        df.rename(columns=rename_map, inplace=True)

        writer = pd.ExcelWriter(output, engine="xlsxwriter")
        df.to_excel(writer, index=False, sheet_name="Data")

        workbook = writer.book
        worksheet = writer.sheets["Data"]

        header_format = workbook.add_format({
            'bg_color': '#ededed',
            'align': 'left',
            'border': 1
        })

        # Headers stylen
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_format)


        # Add width to columns
        for i, col in enumerate(df.columns):
            max_len = df[col].astype(str).map(len).max()
            max_len = max_len if not pd.isnull(max_len) else len(col)
            worksheet.set_column(i, i, max_len + 2)





        worksheet.autofilter(0, 0, 0, len(df.columns) - 1)
        worksheet.freeze_panes(1, 2)

        # Lookup sheet
        lookup_sheet = workbook.add_worksheet("Lookup_Lists")
        boolean_options = ["Ja", "Nee"]
        for i, opt in enumerate(boolean_options):
            lookup_sheet.write(i, 0, opt)
        workbook.define_name("BooleanList", f"='Lookup_Lists'!$A$1:$A$2")
        # lookup_sheet.hide()

        # Maak een inverse map excel -> internal
        inv_map = {}
        for ec, ic in self.columns_mapping.items():
            inv_map[ec] = ic

        # Enumeraties
        enum_col = 1
        enum_ranges = {}
        created_named_ranges = set()
        for col_num, excel_col_name in enumerate(df.columns):
            if excel_col_name in ["objectType", "identifier"]:
                continue
            internal_key = inv_map[excel_col_name]
            field_meta = self.metadata.get(internal_key, {})
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

        start_row = 1
        end_row = start_row + len(df) - 1

        # Eerste 2 kolommen niet bewerkbaar
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

        # Validatie
        for col_num, excel_col_name in enumerate(df.columns):
            if excel_col_name in ["objectType", "identifier"]:
                continue
            internal_key = inv_map[excel_col_name]
            field_meta = self.metadata.get(internal_key, {})
            # Boolean
            if field_meta.get('type') == 'BOOLEAN':
                worksheet.data_validation(start_row, col_num, end_row, col_num, {
                    "validate": "list",
                    "source": "=BooleanList"
                })
            # Enumeraties
            if internal_key in enum_ranges:
                worksheet.data_validation(start_row, col_num, end_row, col_num, {
                    "validate": "list",
                    "source": f"={enum_ranges[internal_key]}"
                })
            # DATE met 'yyyy'
            if field_meta.get('type') == 'DATE' and field_meta.get('dateFormat') == 'yyyy':
                # Alleen integer validatie, geen date_format, om 1905 probleem te voorkomen
                worksheet.data_validation(start_row, col_num, end_row, col_num, {
                    'validate': 'integer',
                    'criteria': 'between',
                    'minimum': 1900,
                    'maximum': 2100,
                    'error_message': 'Geef een geldig jaar (1900-2100) op.'
                })
                # Geen date format zetten, laat standaard general, anders interpreteert Excel '2000' als datum serial.

        # Conditional formatting voor booleans (optioneel)
        # Als de waarde niet Ja/Nee is, geel maken
        worksheet.conditional_format(start_row, 0, end_row, len(df.columns)-1, {
            'type': 'formula',
            # Deze formule is complex en mogelijk niet perfect.
            # Je kunt eventueel vereenvoudigen door een andere approach.
            'criteria': '=AND(INDIRECT("R"&ROW()&"C"&COLUMN(),FALSE)<>"Ja",INDIRECT("R"&ROW()&"C"&COLUMN(),FALSE)<>"Nee")',
            'format': workbook.add_format({'bg_color': '#FFFF00'})
        })

        writer.close()
        output.seek(0)
        return output
