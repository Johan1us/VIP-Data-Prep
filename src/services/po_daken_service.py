# import logging
# import pandas as pd
# from typing import List, Dict, Any, Optional
# import requests
# import io
# from src.utils.excel_utils import ExcelHandler
#
# logger = logging.getLogger(__name__)
#
# # Probeer de API client te importeren. Deze client is nodig om met de externe API te communiceren.
# try:
#     from .api import get_api_client
#
#     logger.debug("Succesvol get_api_client geïmporteerd")
# except ImportError as e:
#     logger.error(f"Importeren van get_api_client mislukt: {str(e)}")
#     # Als de API client niet gevonden kan worden, stoppen we direct.
#     raise ImportError("Vereiste afhankelijkheid 'get_api_client' niet gevonden.")
#
#
# class PODakenService:
#     """
#     Deze serviceklasse beheert PO (Planmatig Onderhoud) Daken gegevens.
#
#     Het doel van deze service:
#     - Ophalen van gebouwgegevens via een externe API.
#     - Exporteren van gebouwgegevens naar Excel.
#     - Valideren en verwerken van geüploade Excel-bestanden met PO Daken data.
#     - In batches bijwerken van gebouwgegevens via de API.
#     """
#
#     # Definitie van metadata voor de daken-attributen:
#     # - naam in het systeem
#     # - type van de waarde (STRING, BOOLEAN)
#     # - toegestane waardes (indien van toepassing)
#     METADATA = {
#         "dakpartner": {
#             "name": "Dakpartner - Building - Woonstad Rotterdam",
#             "type": "STRING",
#             "attributeValueOptions": [
#                 "Cazdak Dakbedekkingen BV",
#                 "Oranjedak West BV",
#                 "Voormolen Dakbedekkingen B.V.",
#             ],
#         },
#         "projectleider": {
#             "name": "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam",
#             "type": "STRING",
#             "attributeValueOptions": ["Jack Robbemond", "Anton Jansen"],
#         },
#         "dakveiligheid": {
#             "name": "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
#             "type": "BOOLEAN",
#         },
#         "antenne": {
#             "name": "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
#             "type": "BOOLEAN",
#         },
#     }
#
#     def __init__(self):
#         """
#         Initialiseer de service:
#         - Verbind met de API via de API-client.
#         - Maak een ExcelHandler om Excel-bestanden te kunnen exporteren en valideren.
#         """
#         logger.info("Initialiseren van PODakenService")
#
#         # Maak verbinding met de API
#         try:
#             self.api_client = get_api_client()
#             logger.debug("API-client succesvol geïnitialiseerd")
#         except Exception as e:
#             error_msg = f"Kan geen verbinding maken met API: {str(e)}"
#             logger.error(error_msg)
#             raise RuntimeError(error_msg)
#
#         # Initialiseer ExcelHandler met onze METADATA.
#         # Deze handler helpt bij het maken en verwerken van Excel bestanden.
#         self.excel_handler = ExcelHandler(self.METADATA)
#
#     def get_all_buildings(self) -> Optional[List[Dict[str, Any]]]:
#         """
#         Haal een lijst met alle gebouwen op via de API.
#
#         Returns:
#             Een lijst met gebouwen (dict) indien succesvol,
#             of None als er iets misgaat.
#         """
#         logger.info("Start met het ophalen van alle gebouwen...")
#         API_URL = "https://api.accept.luxsinsights.com/v1/objects/filterByObjectType"
#
#         try:
#             # 1. Verwerf een token via de API-client (authenticatie)
#             token = self.api_client.authenticate()
#             if not token:
#                 logger.error("Kan niet inloggen bij API (geen token ontvangen)")
#                 return None
#
#             # 2. Stel de headers en parameters in voor de GET-aanroep
#             headers = {
#                 "Accept": "application/json",
#                 "Authorization": f"Bearer {token}"
#             }
#             params = {"objectType": "Building", "pageSize": 10000}
#
#             # 3. Voer de GET-request uit
#             response = requests.get(API_URL, headers=headers, params=params)
#
#             # 4. Controleer de response
#             if response.status_code == 200:
#                 buildings = response.json()
#                 logger.info(f"{len(buildings)} gebouwen opgehaald")
#                 return buildings
#             else:
#                 logger.error(f"API gaf foutcode: {response.status_code}")
#                 logger.error(f"Foutmelding: {response.text}")
#                 return None
#
#         except Exception as e:
#             logger.error(f"Er ging iets mis bij het ophalen van gebouwen: {str(e)}")
#             return None
#
#     def export_to_excel(self, data: List[Dict[str, Any]]) -> io.BytesIO:
#         """
#         Exporteer een lijst met gebouwen naar een Excel-bestand.
#
#         Args:
#             data (List[Dict[str, Any]]): Lijst met gebouwen (dicts).
#
#         Returns:
#             io.BytesIO: Een BytesIO object met de Excel-inhoud.
#         """
#         # De ExcelHandler verzorgt het aanmaken van het Excel bestand.
#         return self.excel_handler.create_excel_file(data)
#
#     def process_uploaded_data(self, df: pd.DataFrame) -> bool:
#         """
#         Verwerk geüploade Excel-gegevens.
#
#         Stappen:
#         - Valideer de data (waardes, types).
#         - Converteer en normaliseer data (bijvoorbeeld booleans, jaartallen).
#         - Creëer een gestructureerde lijst met bijwerkverzoeken.
#         - Verstuur deze in batches naar de API via self.update_buildings_in_batches.
#
#         Args:
#             df (pd.DataFrame): DataFrame met de geüploade gegevens.
#
#         Returns:
#             bool: True als de updates succesvol verwerkt zijn, anders False.
#         """
#         logger.info("Verwerken van geüploade gegevens")
#
#         try:
#             # Valideer de kolommen en waardes in de dataframe
#             self._validate_data(df)
#
#             # Lijst om de gestructureerde update-dictionaries in op te slaan
#             update_data = []
#
#             # Doorloop elke rij in de DataFrame om deze om te zetten naar een update object
#             for _, row in df.iterrows():
#
#                 # Verwerk het jaar van het laatste dakonderhoud
#                 jaar_onderhoud = row["Jaar laatste dakonderhoud - Building - Woonstad Rotterdam"]
#                 if pd.isna(jaar_onderhoud) or pd.isnull(jaar_onderhoud):
#                     # Als er geen jaar is, zet hem op None
#                     jaar_onderhoud = None
#                 else:
#                     # Probeer jaartal te bepalen uit tekst of getal
#                     try:
#                         # Controleer op ISO-formaat (bevat 'T')
#                         if isinstance(jaar_onderhoud, str) and 'T' in jaar_onderhoud:
#                             # Converteer naar datetime en haal alleen het jaar
#                             jaar_onderhoud = str(pd.to_datetime(jaar_onderhoud).year)
#                         else:
#                             # Behandel jaar als een getal (float/int)
#                             jaar_onderhoud = str(int(float(jaar_onderhoud)))
#                     except:
#                         # Als het niet lukt, zet None
#                         jaar_onderhoud = None
#
#                 # Verwerk boolean waarden voor dakveiligheid
#                 dakveiligheid = str(
#                     row["Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam"]).lower()
#                 if pd.isna(dakveiligheid) or pd.isnull(dakveiligheid):
#                     dakveiligheid = None
#                 elif dakveiligheid in ['true', '1', 'yes', 'ja']:
#                     dakveiligheid = "true"
#                 else:
#                     dakveiligheid = "false"
#
#                 # Verwerk boolean waarden voor antenne
#                 antenne = str(row["Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam"]).lower()
#                 if pd.isna(antenne) or pd.isnull(antenne):
#                     antenne = None
#                 elif antenne in ['true', '1', 'yes', 'ja']:
#                     antenne = "true"
#                 else:
#                     antenne = "false"
#
#                 # Bouw het update object op voor deze building
#                 building_update = {
#                     "objectType": "Building",
#                     "identifier": str(row["identifier"]),
#                     "attributes": {
#                         "Dakpartner - Building - Woonstad Rotterdam":
#                             str(row["Dakpartner - Building - Woonstad Rotterdam"])
#                             if not pd.isna(row["Dakpartner - Building - Woonstad Rotterdam"]) else None,
#                         "Jaar laatste dakonderhoud - Building - Woonstad Rotterdam": jaar_onderhoud,
#                         "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam":
#                             str(row["Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"])
#                             if not pd.isna(row[
#                                                "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"]) else None,
#                         "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam": dakveiligheid,
#                         "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam": antenne
#                     }
#                 }
#
#                 # Voeg toe aan onze lijst met updates
#                 update_data.append(building_update)
#
#             # Update de gebouwen in batches via de API
#             return self.update_buildings_in_batches(update_data)
#
#         except Exception as e:
#             logger.error(f"Fout bij het verwerken van geüploade gegevens: {str(e)}")
#             raise
#
#     def _validate_data(self, df: pd.DataFrame) -> None:
#         """
#         Controleer of de DataFrame geldige waarden bevat:
#         - Controleer of dakpartner en projectleider valide opties zijn.
#         - Controleer of boolean kolommen valide boolean waarden bevatten.
#
#         Args:
#             df (pd.DataFrame): De DataFrame met te valideren gegevens.
#
#         Raises:
#             ValueError: Als er ongeldige waarden worden gevonden.
#         """
#         # Zet NaN om naar None voor gemakkelijke validatie
#         df = df.where(pd.notnull(df), None)
#
#         # Controleer Dakpartner
#         valid_dakpartners = self.METADATA["dakpartner"]["attributeValueOptions"]
#         invalid_dakpartners = df[
#             df["Dakpartner - Building - Woonstad Rotterdam"].notna() &
#             ~df["Dakpartner - Building - Woonstad Rotterdam"].isin(valid_dakpartners)
#             ]
#         if not invalid_dakpartners.empty:
#             invalid_values = invalid_dakpartners["Dakpartner - Building - Woonstad Rotterdam"].unique()
#             raise ValueError(
#                 f"Ongeldige Dakpartner waarden gevonden: {invalid_values}. "
#                 f"Verwachte waarden zijn: {valid_dakpartners}."
#             )
#
#         # Controleer Projectleider
#         valid_projectleiders = self.METADATA["projectleider"]["attributeValueOptions"]
#         invalid_projectleiders = df[
#             df["Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"].notna() &
#             ~df["Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"].isin(valid_projectleiders)
#             ]
#         if not invalid_projectleiders.empty:
#             invalid_values = invalid_projectleiders[
#                 "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam"].unique()
#             raise ValueError(
#                 f"Ongeldige Projectleider waarden gevonden: {invalid_values}. "
#                 f"Verwachte waarden zijn: {valid_projectleiders}."
#             )
#
#         # Controleer boolean kolommen
#         boolean_columns = [
#             "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
#             "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam"
#         ]
#         valid_boolean_values = [True, False, "TRUE", "FALSE", "Ja", "Nee", 1, 0, None]
#         for col_name in boolean_columns:
#             if col_name in df.columns:
#                 # Zoek naar ongeldige boolean waarden in deze kolom
#                 invalid_bools = df[~df[col_name].isin(valid_boolean_values)]
#                 if not invalid_bools.empty:
#                     invalid_values = invalid_bools[col_name].fillna("leeg").unique()
#                     raise ValueError(
#                         f"Ongeldige boolean waarden gevonden in '{col_name}': {invalid_values}. "
#                         f"Verwachte waarden zijn: {valid_boolean_values}."
#                     )
#
#     def update_buildings_in_batches(self,
#                                     buildings_data: List[Dict[str, Any]],
#                                     batch_size: int = 100,
#                                     max_retries: int = 3) -> bool:
#         """
#         Werk de gebouwen in batches bij via de API.
#         Als een batch mislukt, probeer het tot max_retries keer.
#
#         Args:
#             buildings_data (List[Dict[str, Any]]): Lijst met gebouwenupdates.
#             batch_size (int): Aantal gebouwen per batch.
#             max_retries (int): Aantal pogingen per batch bij fouten.
#
#         Returns:
#             bool: True als alle batches succesvol bijgewerkt zijn, anders False.
#         """
#         total_buildings = len(buildings_data)
#         successful_updates = 0
#         failed_updates = 0
#         failed_buildings = []
#
#         # Doorloop de lijst in stukken van batch_size
#         for i in range(0, total_buildings, batch_size):
#             batch = buildings_data[i:i + batch_size]
#             success = False
#             attempts = 0
#
#             batch_number = (i // batch_size) + 1
#             logger.info(f"Start met het bijwerken van batch {batch_number} met {len(batch)} gebouwen.")
#
#             # Log de data die naar de API gestuurd wordt, voor debugging
#             logger.debug(f"Request data voor batch {batch_number}:")
#             for building in batch:
#                 logger.debug(f"Building {building['identifier']}: {building}")
#
#             # Probeer tot max_retries om de batch bij te werken
#             while not success and attempts < max_retries:
#                 attempts += 1
#                 try:
#                     # Stuur de update naar de API
#                     api_success = self.api_client.update_buildings(batch)
#
#                     if api_success:
#                         # Als het lukt, markeer als success en tel de successen
#                         success = True
#                         successful_updates += len(batch)
#                         logger.info(f"Batch {batch_number} succesvol bijgewerkt bij poging {attempts}.")
#                     else:
#                         # Als de API niet succesvol is, registreer de mislukte gebouwen
#                         failed_updates += len(batch)
#                         for building in batch:
#                             failed_buildings.append({
#                                 'identifier': building['identifier'],
#                                 'message': 'API update failed'
#                             })
#                         logger.error(f"Batch {batch_number} mislukt bij poging {attempts}")
#
#                 except Exception as e:
#                     # Als er een uitzondering optreedt, log dit en probeer later opnieuw (tot max_retries)
#                     logger.error(f"Uitzondering opgetreden bij het bijwerken van batch {batch_number} "
#                                  f"bij poging {attempts}: {str(e)}")
#
#             # Als zelfs na max_retries niet gelukt, stop dan en geef False terug.
#             if not success:
#                 logger.error(f"Niet gelukt om batch {batch_number} bij te werken na {max_retries} pogingen.")
#                 return False
#
#         # Als alle batches geprobeerd zijn, log een samenvatting
#         logger.info("=== Eindrapportage van de upload ===")
#         logger.info(f"Totaal aantal gebouwen: {total_buildings}")
#         logger.info(f"Succesvol bijgewerkt: {successful_updates}")
#         logger.info(f"Mislukt: {failed_updates}")
#         if failed_buildings:
#             logger.info("Mislukte updates:")
#             for failed in failed_buildings:
#                 logger.info(f"- Building {failed['identifier']}: {failed['message']}")
#         logger.info("===================================")
#
#         return True

# from api.api_client import get_api_client
# from services.api import get_api_client
from utils.excel_utils_ import ExcelHandler
from services.base_service import BasePOService
from configuratie.config_po_daken import METADATA_DAKEN, COLUMNS_MAPPING_DAKEN

class PODakenService(BasePOService):
    def __init__(self, luxs_api_client):
        excel_handler = ExcelHandler(METADATA_DAKEN, COLUMNS_MAPPING_DAKEN)
        super().__init__(luxs_api_client, excel_handler, METADATA_DAKEN, COLUMNS_MAPPING_DAKEN)
