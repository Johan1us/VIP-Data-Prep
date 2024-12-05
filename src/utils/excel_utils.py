from typing import Any, Dict, List, Optional
import pandas as pd
import io
import logging
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

# Initialiseer de logger
logger = logging.getLogger(__name__)

class ExcelHandler:
    def __init__(self, metadata: Dict[str, Any]):
        # Sla de metadata op
        self.metadata = metadata

        # Definieer de vereiste kolommen
        self.required_columns = [
            "objectType",
            "identifier",
            "Dakpartner - Building - Woonstad Rotterdam",
            "Jaar laatste dakonderhoud - Building - Woonstad Rotterdam",
            "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam",
            "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
            "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
        ]

    def create_excel_file(self, data: List[Dict[str, Any]], output: Optional[io.BytesIO] = None) -> io.BytesIO:
        """
        Maak een Excel-bestand met gegevensvalidatie en retourneer het als een BytesIO-object.

        Parameters:
        - data: Een lijst met gegevens in de vorm van dictionaries.
        - output: Een optioneel BytesIO-object om het Excel-bestand in op te slaan.

        Retourneert:
        - Een BytesIO-object met het gegenereerde Excel-bestand.
        """

        # Controleer of er data is om te exporteren
        if not data:
            logger.error("Geen data om te exporteren")
            raise ValueError("Geen data om te exporteren")

        try:
            # Maak een nieuw BytesIO-object als er geen output is opgegeven
            if output is None:
                output = io.BytesIO()

            # Maak een DataFrame van de data
            df = pd.DataFrame(data)

            # Splits de 'attributes' kolom uit in aparte kolommen
            df_attributes = df['attributes'].apply(pd.Series)
            df = pd.concat([df.drop(['attributes'], axis=1), df_attributes], axis=1)

            # Converteer boolean kolommen naar Ja/Nee
            boolean_columns = [
                "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
                "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
            ]
            for col in boolean_columns:
                if col in df.columns:
                    # Voeg logging toe om te zien wat er in de kolom zit
                    logger.debug(f"Unieke waarden in {col}: {df[col].unique()}")

                    # Map verschillende mogelijke boolean waarden naar Ja/Nee
                    df[col] = df[col].map({
                        'true': 'Ja',
                        'false': 'Nee',
                    }, na_action='ignore')

                    # Log het resultaat
                    logger.debug(f"Unieke waarden na conversie in {col}: {df[col].unique()}")

            # Converteer de datumkolom naar UTC en haal het jaar op
            jaar_kolom = 'Jaar laatste dakonderhoud - Building - Woonstad Rotterdam'
            if jaar_kolom in df.columns:
                try:
                    df[jaar_kolom] = pd.to_datetime(
                        df[jaar_kolom],
                        utc=True,
                        errors='coerce'
                    ).dt.tz_convert('Europe/Amsterdam').dt.year.astype('Int64')
                except Exception as e:
                    logger.warning(f"Kon de datumkolom niet converteren: {str(e)}")

            # Houd alleen de vereiste kolommen over
            df = df[self.required_columns]

            # Maak een ExcelWriter object met xlsxwriter engine
            writer = pd.ExcelWriter(output, engine="xlsxwriter")

            # Schrijf de DataFrame naar het Excel-bestand
            df.to_excel(writer, index=False, sheet_name="Data")

            # Voeg gegevensvalidatie toe aan het Excel-bestand
            self._add_excel_validation(writer, df)

            # Sla het Excel-bestand op en retourneer het
            writer.close()
            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Fout bij het maken van het Excel-bestand: {str(e)}")
            raise

    def _add_excel_validation(self, writer: pd.ExcelWriter, df: pd.DataFrame) -> None:
        """
        Voeg gegevensvalidatie toe aan het Excel-bestand.

        Parameters:
        - writer: Het ExcelWriter-object.
        - df: De DataFrame met de gegevens.
        """

        # Haal het workbook en de worksheet op
        workbook = writer.book
        worksheet = writer.sheets["Data"]

        # Maak formaten voor de cellen
        header_format = workbook.add_format({
            'bg_color': '#ededed',  # Lichtgrijs
            'align': 'left',        # Links uitlijnen
            'border': 1,            # Dunne rand
            'locked': False          # Header cellen zijn niet vergrendeld
        })

        unlocked_format = workbook.add_format({'locked': False, 'align': 'right'})

        # Pas het header formaat toe op de header rij
        for col_num, value in enumerate(self.required_columns):
            worksheet.write(0, col_num, value, header_format)

        # Pas het ontgrendelde formaat toe op alle kolommen A t/m G
        worksheet.set_column('A:B', 15, unlocked_format)
        worksheet.set_column('C:G', 30, unlocked_format)

        # Voeg filters toe aan de eerste rij
        worksheet.autofilter(0, 0, 0, len(self.required_columns) - 1)

        # Bevries de eerste rij en kolommen A & B
        worksheet.freeze_panes(1, 2)

        # Bescherm het werkblad met sorteer- en filteropties ingeschakeld
        worksheet.protect('', {
            'sort': True,
            'autofilter': True,
            'select_locked_cells': True,
            'select_unlocked_cells': True,
            'format_cells': False,
            'format_columns': False,
            'format_rows': False,
            'insert_columns': False,
            'insert_rows': False,
            'delete_columns': False,
            'delete_rows': False,
        })

        # Maak een nieuwe worksheet voor de validatielijsten
        lookup_sheet = workbook.add_worksheet("Lookup_Lists")

        # Voeg validatielijsten toe
        self._add_validation_lists(workbook, lookup_sheet)

        # Verberg de "Lookup_Lists" worksheet
        lookup_sheet.hide()

        # Definieer de start- en eindrij voor de validatie (exclusief de header)
        start_row = 1  # Eerste rij na de header
        end_row = start_row + len(df) - 1  # Correcte laatste rij

        # Voeg kolomvalidatie toe
        self._add_column_validation(worksheet, start_row, end_row)

    def _add_validation_lists(self, workbook: Workbook, lookup_sheet: Worksheet) -> None:
        """
        Voeg validatielijsten toe aan de lookup sheet.

        Parameters:
        - workbook: Het Workbook-object.
        - lookup_sheet: De Worksheet voor de validatielijsten.
        """

        # Voeg 'Dakpartner' opties toe
        dakpartner_options = self.metadata["dakpartner"]["attributeValueOptions"]
        for row_num, option in enumerate(dakpartner_options):
            lookup_sheet.write(row_num, 0, option)
        workbook.define_name(
            "DakpartnerList",
            f"='Lookup_Lists'!$A$1:$A${len(dakpartner_options)}"
        )

        # Voeg 'Projectleider' opties toe
        projectleider_options = self.metadata["projectleider"]["attributeValueOptions"]
        for row_num, option in enumerate(projectleider_options):
            lookup_sheet.write(row_num, 1, option)
        workbook.define_name(
            "ProjectleiderList",
            f"='Lookup_Lists'!$B$1:$B${len(projectleider_options)}"
        )

        # Voeg 'Ja' en 'Nee' opties toe
        boolean_options = ["Ja", "Nee"]
        for row_num, option in enumerate(boolean_options):
            lookup_sheet.write(row_num, 2, option)
        workbook.define_name(
            "BooleanList",
            f"='Lookup_Lists'!$C$1:$C${len(boolean_options)}"
        )

    def _add_column_validation(self, worksheet: Worksheet, start_row: int, end_row: int) -> None:
        """
        Voeg gegevensvalidatie toe aan specifieke kolommen.

        Parameters:
        - worksheet: De Worksheet waar validatie moet worden toegepast.
        - start_row: De start rij voor validatie.
        - end_row: De eind rij voor validatie.
        """

        # Voeg waarschuwing toe voor kolommen A en B
        for col in [0, 1]:  # Kolommen A en B
            worksheet.data_validation(
                start_row,
                col,
                end_row,
                col,
                {
                    'validate': 'any',
                    'input_title': 'Let op!',
                    'input_message': 'Deze kolom mag niet worden aangepast.',
                    'show_input': True
                }
            )

        # Validatie voor 'Dakpartner' kolom
        dakpartner_col = self.required_columns.index("Dakpartner - Building - Woonstad Rotterdam")
        worksheet.data_validation(
            start_row,
            dakpartner_col,
            end_row,
            dakpartner_col,
            {
                "validate": "list",
                "source": "=DakpartnerList",
                "error_message": "Ongeldige invoer. Kies een Dakpartner uit de lijst."
            }
        )

        # Validatie voor 'Projectleider' kolom
        projectleider_col = self.required_columns.index(
            "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"
        )
        worksheet.data_validation(
            start_row,
            projectleider_col,
            end_row,
            projectleider_col,
            {
                "validate": "list",
                "source": "=ProjectleiderList",
                "error_message": "Ongeldige invoer. Kies een Projectleider uit de lijst."
            }
        )

        # Validatie voor Booleaanse kolommen
        boolean_columns = [
            "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
            "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
        ]
        for col_name in boolean_columns:
            col_index = self.required_columns.index(col_name)
            worksheet.data_validation(
                start_row,
                col_index,
                end_row,
                col_index,
                {
                    "validate": "list",
                    "source": "=BooleanList",
                    "error_message": "Ongeldige invoer. Kies Ja of Nee."
                }
            )

        # Validatie voor de jaar kolom
        jaar_col = self.required_columns.index("Jaar laatste dakonderhoud - Building - Woonstad Rotterdam")
        worksheet.data_validation(
            start_row,
            jaar_col,
            end_row,
            jaar_col,
            {
                "validate": "integer",
                "criteria": "between",
                "minimum": 1900,
                "maximum": 2100,
                "error_message": "Ongeldig jaartal. Voer een jaartal in tussen 1900 en 2100."
            }
        )
