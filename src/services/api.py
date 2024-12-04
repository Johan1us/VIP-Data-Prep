import pandas as pd
from api_client import LuxsAcceptClient

def prepare_api_payload(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to API payload format"""
    payload = []
    for _, row in df.iterrows():
        object_data = {
            "objectType": "Unit",
            "identifier": row["identifier"],
            "parentObjectType": "Building",
            "parentIdentifier": row["parentIdentifier"],
            "attributes": {},
        }

        # Convert all other columns to attributes
        for column in df.columns:
            if column not in ["identifier", "parentIdentifier"]:
                object_data["attributes"][column] = str(row[column])

        payload.append(object_data)

    return payload

def get_api_client():
    return LuxsAcceptClient()
