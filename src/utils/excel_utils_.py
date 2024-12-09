from typing import Any, Dict, List, Optional
import pandas as pd
import io
import logging
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

logger = logging.getLogger(__name__)


class ExcelHandler:
    def __init__(self,
                 metadata: Dict[str, Any],
                 columns_mapping: Dict[str, str]):
        """
        Genereer een Excel-bestand op basis van meegegeven metadata en kolomnamen.
        """
        logger.debug("Initialiseren van ExcelHandler...")
        self.metadata = metadata
        self.columns_mapping = columns_mapping
        # Inverse mapping: interne key -> Excel kolomnaam
        self.inverse_mapping = {v: k for k, v in columns_mapping.items()}
        self.required_columns = list(columns_mapping.values())  # Dit zijn de interne keys
        logger.debug("ExcelHandler geïnitialiseerd.")

    def create_excel_file(self, data: List[Dict[str, Any]], output: Optional[io.BytesIO] = None) -> io.BytesIO:

        logger.debug("Exporteren van data naar Excel...")
        logger.debug(f"Eerste paar records: {data[:2]}")

        if not data:
            logger.error("Geen data om te exporteren")
            raise ValueError("Geen data om te exporteren")

        try:
            if output is None:
                output = io.BytesIO()
            logger.debug(f"Converteer naar DataFrame...")
            df = pd.DataFrame(data)

            # Extract attributes en hernoem direct naar interne keys
            if 'attributes' in df.columns:
                df_attributes = df['attributes'].apply(pd.Series)
                # Maak een mapping van externe naam -> interne key
                rename_map = {v['name']: k for k, v in self.metadata.items() if 'name' in v}
                df_attributes.rename(columns=rename_map, inplace=True)
                df = pd.concat([df.drop(['attributes'], axis=1), df_attributes], axis=1)

            # Boolean velden converteren
            boolean_fields = [k for k, v in self.metadata.items() if v.get('type') == 'BOOLEAN']
            for key in boolean_fields:
                if key in df.columns:
                    logger.debug(f"Converteer boolean veld {key} naar Ja/Nee")
                    df[key] = df[key].map({'true': 'Ja', 'false': 'Nee'}, na_action='ignore')

            # Jaar velden converteren indien nodig
            for key, field_meta in self.metadata.items():
                if key in df.columns and field_meta.get('extra_processing') == 'convert_to_year':
                    try:
                        df[key] = (
                            pd.to_datetime(df[key], utc=True, errors='coerce')
                            .dt.tz_convert('Europe/Amsterdam')
                            .dt.year
                            .astype('Int64')
                        )
                    except Exception as e:
                        logger.warning(f"Kon de jaar-kolom niet converteren ({key}): {str(e)}")

            logger.debug(f"Kolommen: {df.columns}")
            logger.debug(f"Eerste paar records: {df.head(2)}")
            logger.debug(f"Verplichte kolommen: {self.required_columns}")
            # Filter op interne keys
            df = df[self.required_columns]

            # Nu hernoemen naar externe kolomnamen
            df.rename(columns=self.inverse_mapping, inplace=True)

            writer = pd.ExcelWriter(output, engine="xlsxwriter")
            df.to_excel(writer, index=False, sheet_name="Data")

            self._add_excel_validation(writer, df)

            writer.close()
            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Fout bij het maken van het Excel-bestand: {str(e)}")
            raise

    def _internal_keys_to_excel_colnames(self, internal_keys: List[str]) -> List[str]:
        """
        Deze hulpfunctie geeft de lijst van interne keys terug.
        Op dit moment gaan we ervan uit dat de DataFrame-kolommen reeds overeenkomen met deze interne keys.
        Als dat niet het geval is, moet je hier extra logica toevoegen om de juiste kolomnamen te bepalen.
        """
        return internal_keys

    def _add_excel_validation(self, writer: pd.ExcelWriter, df: pd.DataFrame) -> None:
        workbook = writer.book
        worksheet = writer.sheets["Data"]

        header_format = workbook.add_format({
            'bg_color': '#ededed',
            'align': 'left',
            'border': 1,
            'locked': False
        })
        unlocked_format = workbook.add_format({'locked': False, 'align': 'right'})

        # Headers stylen (df columns zijn nu de uiteindelijke Excel kolomnamen)
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_format)

        worksheet.set_column('A:B', 15, unlocked_format)
        if len(df.columns) > 2:
            worksheet.set_column(2, len(df.columns) - 1, 30, unlocked_format)

        worksheet.autofilter(0, 0, 0, len(df.columns) - 1)
        worksheet.freeze_panes(1, 2)
        worksheet.protect('', {
            'sort': True,
            'autofilter': True,
            'select_locked_cells': True,
            'select_unlocked_cells': True
        })

        lookup_sheet = workbook.add_worksheet("Lookup_Lists")
        self._add_validation_lists(workbook, lookup_sheet)
        lookup_sheet.hide()

        start_row = 1
        end_row = start_row + len(df) - 1

        self._add_column_validation(worksheet, start_row, end_row, df)

    def _add_validation_lists(self, workbook: Workbook, lookup_sheet: Worksheet) -> None:
        boolean_options = ["Ja", "Nee"]
        for row_num, option in enumerate(boolean_options):
            lookup_sheet.write(row_num, 0, option)
        workbook.define_name("BooleanList", f"='Lookup_Lists'!$A$1:$A${len(boolean_options)}")

        col_index = 1
        for key, field_meta in self.metadata.items():
            if 'attributeValueOptions' in field_meta:
                options = field_meta['attributeValueOptions']
                for row_num, option in enumerate(options):
                    lookup_sheet.write(row_num, col_index, option)
                list_name = f"{key}List"
                range_end = len(options)
                workbook.define_name(
                    list_name,
                    f"='Lookup_Lists'!${chr(ord('A') + col_index)}$1:${chr(ord('A') + col_index)}${range_end}"
                )
                col_index += 1

    def _add_column_validation(self, worksheet: Worksheet, start_row: int, end_row: int, df: pd.DataFrame) -> None:
        # Eerste 2 kolommen (objectType, identifier) niet bewerkbaar
        # Hier kun je ook ervoor kiezen in metadata aan te geven dat bepaalde kolommen niet bewerkt mogen worden.
        # Als je echt alles dynamisch wilt, zou je een "editable": False kunnen toevoegen in metadata
        # en dat hier checken. Voor nu laten we deze logica even staan. Dat is niet hardcoded op jaartallen.
        for col in range(min(2, df.shape[1])):
            worksheet.data_validation(
                start_row, col, end_row, col,
                {
                    'validate': 'any',
                    'input_title': 'Let op!',
                    'input_message': 'Deze kolom mag niet worden aangepast.',
                    'show_input': True
                }
            )

        # Rest van de kolommen
        for col_num, excel_col_name in enumerate(df.columns):
            # Vind bijbehorende interne key
            key = self.columns_mapping[excel_col_name]
            field_meta = self.metadata.get(key, {})

            # Check op attributeValueOptions (dropdown)
            if 'attributeValueOptions' in field_meta:
                worksheet.data_validation(
                    start_row, col_num, end_row, col_num,
                    {
                        "validate": "list",
                        "source": f"={key}List",
                        "error_message": "Ongeldige invoer. Kies uit de lijst."
                    }
                )
            # BOOLEAN
            elif field_meta.get('type') == 'BOOLEAN':
                worksheet.data_validation(
                    start_row, col_num, end_row, col_num,
                    {
                        "validate": "list",
                        "source": "=BooleanList",
                        "error_message": "Ongeldige invoer. Kies Ja of Nee."
                    }
                )
            # Algemene validatie uit metadata
            elif 'validation' in field_meta:
                validation_config = field_meta['validation']
                worksheet.data_validation(
                    start_row, col_num, end_row, col_num,
                    validation_config
                )
            # Geen extra validatie nodig? Dan doen we niets.

    def _get_excel_column_name_from_key(self, key: str) -> Optional[str]:
        # Inverse lookup: interne key -> Excel kolomnaam
        return self.columns_mapping.get(key)
