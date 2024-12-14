# app/main.py
from VIP_DataMakelaar.app.utils.api_client import APIClient
from VIP_DataMakelaar.app.utils.config_loader import ConfigLoader
from VIP_DataMakelaar.app.utils.excel_utils import ExcelHandler
import os

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


if __name__ == "__main__":
    # Stel je client_id en secret in, bijv. via environment variables
    client_id = os.getenv("LUXS_ACCEPT_CLIENT_ID")
    client_secret = os.getenv("LUXS_ACCEPT_CLIENT_SECRET")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret}")

    client = APIClient(client_id=client_id, client_secret=client_secret)
    print(f"Client: {client}")

    loader = ConfigLoader()

    # Kies een dataset, bv "po_daken"
    config = loader.load_config("po_daken")
    print(f"Config: {type(config)}")
    print(f"Config: {config}")

    # Haal metadata
    metadata = client.get_metadata(object_type=config["objectType"])
    print(f"Metadata: {type(metadata)}")
    print(f"Metadata: {metadata}")

    # Haal data op
    data = client.get_objects(object_type=config["objectType"], only_active=True)
    print(f"Data: {type(data)}")
    print(f"Data: {len(data)}")
    # print the first 5 records
    for record in data[:5]:
        print(record)

    columns_mapping = {attr["excelColumnName"]: attr["AttributeName"] for attr in config["attributes"]}
    print(f"Columns mapping: {columns_mapping}")

    # Maak de meta_map
    metadata_map = build_metadata_map(metadata, config)
    print(f"Metadata map: {metadata_map}")

    handler = ExcelHandler(metadata=metadata_map, columns_mapping=columns_mapping)
    excel_file = handler.create_excel_file(data=data)

    # Excel genereren
    # excel_file = ExcelHandler.create_excel_file(data, config, metadata)
    print(f"Excel bestand: {excel_file}")

    # Schrijf weg naar een bestand
    with open("output.xlsx", "wb") as f:
        f.write(excel_file.read())

    print("Excel bestand gegenereerd: output.xlsx")
