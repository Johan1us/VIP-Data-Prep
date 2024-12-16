import streamlit as st
from VIP_DataMakelaar.app.utils.api_client import APIClient
from VIP_DataMakelaar.app.utils.excel_utils import ExcelHandler
from VIP_DataMakelaar.app.utils.validation import ExcelValidator
import io
import pandas as pd
import os
import json

def load_css():
    try:
        css_file = os.path.join(os.path.dirname(__file__), "assets", "css", "style.css")
        if os.path.exists(css_file):
            with open(css_file) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        else:
            st.warning(f"CSS bestand niet gevonden op pad: {css_file}")
            # Gebruik een basis CSS als fallback
            st.markdown("""
                <style>
                    .stButton>button {
                        background-color: #0066cc;
                        color: white;
                        border-radius: 4px;
                        padding: 0.5rem 1rem;
                        border: none;
                    }
                    .stButton>button:hover {
                        background-color: #0052a3;
                    }
                </style>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Kon CSS niet laden: {str(e)}")
        # Gebruik dezelfde fallback CSS als hierboven

class DatasetManager:
    def __init__(self, config_folder):
        self.config_folder = config_folder
        self.api_client = self._initialize_api_client()

    def _initialize_api_client(self):
        client_id = os.getenv("LUXS_ACCEPT_CLIENT_ID")
        client_secret = os.getenv("LUXS_ACCEPT_CLIENT_SECRET")
        base_url = "https://api.accept.luxsinsights.com"
        return APIClient(client_id=client_id, client_secret=client_secret, base_url=base_url)

    def get_available_datasets(self):
        datasets = []
        for file in os.listdir(self.config_folder):
            if file.endswith(".json"):
                with open(os.path.join(self.config_folder, file), 'r') as f:
                    data = json.load(f)
                    datasets.append(data["dataset"])
        return ["Geen dataset geselecteerd"] + datasets

    def get_dataset_config(self, dataset_name):
        for file in os.listdir(self.config_folder):
            if file.endswith(".json"):
                with open(os.path.join(self.config_folder, file), 'r') as f:
                    data = json.load(f)
                    if data["dataset"] == dataset_name:
                        return data
        return None

    def get_object_type(self, dataset_name):
        for file in os.listdir(self.config_folder):
            if file.endswith(".json"):
                with open(os.path.join(self.config_folder, file), 'r') as f:
                    data = json.load(f)
                    if data["dataset"] == dataset_name:
                        return data["objectType"]
        return None

    def get_file_name(self, dataset_name):
        for file in os.listdir(self.config_folder):
            if file.endswith(".json"):
                with open(os.path.join(self.config_folder, file), 'r') as f:
                    data = json.load(f)
                    if data["dataset"] == dataset_name:
                        return file.replace(".json", "")
        return None

def show_dataset_fields(config):
    excel_columns = [attr["excelColumnName"] for attr in config["attributes"]]
    df = pd.DataFrame(excel_columns, columns=['Velden :'])
    st.dataframe(df, hide_index=True)

def handle_excel_download(config, api_client):
    object_type = config["objectType"]
    attribute_names = [attr["AttributeName"] for attr in config["attributes"]]

    # Get metadata and dataset
    metadata = api_client.get_metadata(object_type)
    response_data = api_client.get_all_objects(
        object_type=object_type,
        attributes=attribute_names,
        only_active=True
    )

    # Extract the actual objects from the response
    dataset_data = response_data.get('objects', [])

    print("Debug dataset_data:")
    print(f"Number of objects: {len(dataset_data)}")
    if dataset_data:
        print(f"First object sample: {dataset_data[0]}")

    # Create and download Excel
    columns_mapping = {attr["excelColumnName"]: attr["AttributeName"] for attr in config["attributes"]}
    metadata_map = build_metadata_map(metadata, config)

    handler = ExcelHandler(metadata=metadata_map, columns_mapping=columns_mapping, object_type=object_type)
    excel_file = handler.create_excel_file(data=dataset_data)

    # Preview van de data
    st.write("Preview van de eerste 5 rijen van de Excel file:")
    preview_df = pd.read_excel(excel_file)
    st.dataframe(preview_df.head(5), hide_index=True)

    return excel_file

def show_home():
    st.title("Welkom bij de VIP DataMakelaar")
    st.write("Je bent ingelogd! Hier kun je datasets selecteren en bewerken.")

    config_folder = os.path.join(os.path.dirname(__file__), "config")
    dataset_manager = DatasetManager(config_folder)

    # Dataset selection
    datasets = dataset_manager.get_available_datasets()
    selected_dataset = st.selectbox("Selecteer een dataset", datasets, index=0)

    if selected_dataset != "Geen dataset geselecteerd":
        config = dataset_manager.get_dataset_config(selected_dataset)
        if config:
            show_dataset_fields(config)

            if st.button("Geneer Excel"):
                st.write(f"Excel voor {selected_dataset} wordt gegenereerd...")
                file_name = dataset_manager.get_file_name(selected_dataset)
                try:
                    excel_file = handle_excel_download(config, dataset_manager.api_client)
                    st.download_button(
                        label="Download Excel",
                        data=excel_file,
                        file_name=f"{file_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error("❌ Er is een fout opgetreden bij het genereren van de Excel:")
                    st.error(f"Foutmelding: {str(e)}")

                    # Toon extra debug informatie
                    with st.expander("Technische details", expanded=False):
                        st.write("📋 Debug informatie:")
                        st.write(f"- Dataset: {selected_dataset}")
                        st.write(f"- Bestandsnaam: {file_name}")
                        st.write(f"- Object Type: {config.get('objectType', 'Niet gevonden')}")
                        st.write(f"- Aantal attributen: {len(config.get('attributes', []))}")
                        st.write(f"- Type fout: {type(e).__name__}")

                        # Als er een traceback beschikbaar is
                        import traceback
                        st.code(traceback.format_exc(), language='python')

                    st.info("💡 Suggestie: Controleer of alle benodigde configuraties correct zijn en of er verbinding is met de API.")

            # Maak een upload veld om de excel file te uploaden zodat deze kan worden gevalideerd
            excel_file = st.file_uploader("Upload Excel", type=["xlsx"])


            if excel_file:
                st.write("Excel file is geupload")

                try:
                    # Lees de Excel file
                    df = pd.read_excel(excel_file)
                    st.write("Preview van de geüploade Excel:")
                    st.dataframe(df.head(5), hide_index=True)

                    # Haal de metadata op voor het objectType
                    object_type = dataset_manager.get_object_type(selected_dataset)
                    metadata = dataset_manager.api_client.get_metadata(object_type)

                    # Zoek het jaar attribuut in de metadata
                    jaar_attribute = next(
                        (attr for attr in metadata.get('objectTypes', [])[0].get('attributes', [])
                         if attr['name'] == 'Jaar laatste dakonderhoud - Building - Woonstad Rotterdam'),
                        None
                    )

                    if jaar_attribute:
                        st.write("📅 Datumformaat configuratie:", jaar_attribute.get('dateFormat', 'Geen datumformaat gevonden'))

                    # Bouw de metadata map en columns mapping
                    columns_mapping = {attr["excelColumnName"]: attr["AttributeName"] for attr in config["attributes"]}
                    metadata_map = build_metadata_map(metadata, config)

                    # Valideer de Excel
                    validator = ExcelValidator(metadata=metadata_map, columns_mapping=columns_mapping, object_type=object_type)
                    validation_errors = validator.validate_excel(df)

                    if validation_errors:
                        st.error("De Excel bevat de volgende fouten:")
                        error_df = pd.DataFrame(validation_errors)
                        st.dataframe(error_df, hide_index=True)
                    else:
                        st.success("De Excel is succesvol gevalideerd! Alle data voldoet aan de vereisten.")

                        if st.button("Verstuur naar API"):
                            try:
                                st.info("Data wordt verstuurd naar de API...")

                                # Convert DataFrame to the expected format and handle non-JSON-compliant values
                                df_clean = df.replace([float('inf'), float('-inf'), float('nan')], None)

                                # Controleer of 'identifier' kolom aanwezig is in de DataFrame
                                if 'identifier' not in df_clean.columns:
                                    raise ValueError("Geen 'identifier' kolom gevonden in de data!")

                                # Prepare data in correct format according to API spec
                                data_to_send = []
                                for _, row in df_clean.iterrows():
                                    attributes = {}
                                    for col, api_field in columns_mapping.items():
                                        value = row[col]
                                        # Speciale behandeling voor het jaartal veld
                                        if "Jaar laatste dakonderhoud" in api_field and pd.notnull(value):
                                            try:
                                                if jaar_attribute and jaar_attribute.get('dateFormat') == 'yyyy':
                                                    # Als het formaat 'yyyy' is, stuur als string
                                                    value = str(int(float(value)))
                                                else:
                                                    # Anders, gebruik het gespecificeerde formaat of een default
                                                    year = int(float(value))
                                                    date_format = jaar_attribute.get('dateFormat', 'dd-MM-yyyy')
                                                    if date_format == 'dd-MM-yyyy':
                                                        value = f"31-12-{year}"
                                                    elif date_format == 'yyyy-MM-dd':
                                                        value = f"{year}-12-31"
                                                    else:
                                                        # Als onbekend formaat, log een waarschuwing
                                                        st.warning(f"Onbekend datumformaat: {date_format}")
                                                        value = str(year)
                                            except (ValueError, TypeError):
                                                value = None
                                        elif pd.notnull(value):
                                            value = str(value)
                                        else:
                                            value = None

                                        attributes[api_field] = value

                                    obj = {
                                        "objectType": object_type,
                                        "identifier": str(row['identifier']),
                                        "attributes": attributes
                                    }
                                    data_to_send.append(obj)

                                # Log request details
                                st.write("🔍 API Request Details:")
                                st.json({
                                    "url": f"{dataset_manager.api_client.base_url}/v1/objects",
                                    "method": "PUT",
                                    "headers": dataset_manager.api_client._headers(),
                                    "request_body_sample": data_to_send[:2]
                                })

                                # Send data to API
                                response = dataset_manager.api_client.update_objects(objects_data=data_to_send)

                                # Log response details
                                st.write("📥 API Response Details:")
                                st.json({
                                    "status_code": 200,
                                    "response_sample": response[:2] if response else None,
                                    "total_objects": len(response) if response else 0,
                                    "successful": sum(1 for r in response if r['success']) if response else 0,
                                    "failed": sum(1 for r in response if not r['success']) if response else 0
                                })

                                if response:
                                    # Toon gedetailleerd rapport
                                    failed_updates = [r for r in response if not r['success']]
                                    if failed_updates:
                                        st.error("❌ Mislukte updates:")
                                        for fail in failed_updates:
                                            st.write(f"- Object {fail['identifier']}: {fail['message']}")

                                    st.success(f"""
                                    ✅ Upload Rapport:
                                    - Totaal aantal objecten: {len(response)}
                                    - Succesvol bijgewerkt: {sum(1 for r in response if r['success'])}
                                    - Mislukt: {sum(1 for r in response if not r['success'])}
                                    """)

                            except Exception as e:
                                st.error(f"❌ Er is een fout opgetreden: {str(e)}")
                                # Print more debug information
                                st.write("Debug informatie:")
                                st.write("Beschikbare kolommen:", df.columns.tolist())
                                st.write("Columns mapping:", columns_mapping)
                                st.write("Config attributes:", config["attributes"])

                except Exception as e:
                    st.error(f"Er is een fout opgetreden bij het valideren: {str(e)}")

    if st.button("Uitloggen"):
        st.session_state["logged_in"] = False
        st.rerun()

def build_metadata_map(metadata: dict, config: dict) -> dict:
    object_type = config["objectType"]
    ot_data = next((ot for ot in metadata["objectTypes"] if ot["name"] == object_type), None)
    if not ot_data:
        raise ValueError(f"Object type {object_type} not found in metadata")

    metadata_by_name = {a["name"]: a for a in ot_data["attributes"]}
    meta_map = {}
    for attr_def in config["attributes"]:
        attr_name = attr_def["AttributeName"]
        meta = metadata_by_name.get(attr_name, {})
        meta_map[attr_name] = meta
    return meta_map

def show_login():
    st.title("Inloggen")
    username = st.text_input("Gebruikersnaam")
    password = st.text_input("Wachtwoord", type="password")
    if st.button("Login"):
        if username == "admin" and password == "secret":  # Dummy credentials
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Ongeldige inloggegevens, probeer opnieuw.")

if "logged_in" not in st.session_state:
    is_ingelogd = True
    st.session_state["logged_in"] = is_ingelogd


if st.session_state["logged_in"]:
    show_home()
else:
    show_login()
