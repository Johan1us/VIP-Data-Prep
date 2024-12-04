import pandas as pd
from typing import Any, Dict, List, Union

def validate_csv_structure(df: pd.DataFrame) -> Dict[str, List[Union[str, Dict[str, str]]]]:
    validation_errors: Dict[str, List[Union[str, Dict[str, str]]]] = {
        "critical": [],
        "warnings": []
    }

    # Check if the dataframe is empty
    if df.empty:
        validation_errors["critical"].append("Het CSV-bestand is leeg")
        return validation_errors

    # Check mandatory columns with their exact names, types and allowed values
    required_columns = {
        "Objecttype": {"type": "STRING"},
        "Clustercode": {"type": "STRING"},
        "Dakpartner": {
            "type": "STRING",
            "allowed_values": [
                "Oranjedak West BV",
                "Cazdak Dakbedekkingen BV",
                "Voormolen Dakbedekkingen B.V.",
            ],
        },
        "Betrokken Projectleider Techniek Daken": {
            "type": "STRING",
            "allowed_values": ["Jack Robbemond", "Anton Jansen"],
        },
        "Jaar laatste dakonderhoud": {"type": "DATE", "date_format": "yyyy"},
        "Dakveiligheidsvoorzieningen aangebracht?": {"type": "BOOLEAN"},
        "Bliksembeveiliging": {"type": "STRING"},
        "Antenneopstelplaats": {"type": "BOOLEAN"},
    }

    # Check for missing columns
    missing_columns = [col for col in required_columns.keys() if col not in df.columns]
    if missing_columns:
        validation_errors["critical"].append(
            {"message": "Ontbrekende verplichte kolommen", "details": missing_columns}
        )

    # Check data types and values for existing columns
    for col, specs in required_columns.items():
        if col in df.columns:
            # Check for empty values
            empty_count = df[col].isna().sum()
            if empty_count > 0:
                validation_errors["warnings"].append(
                    {
                        "message": f"Lege waarden gevonden in kolom '{col}'",
                        "details": f"{empty_count} rijen hebben geen waarde",
                    }
                )

            # Type and value validation
            if specs["type"] == "BOOLEAN":
                invalid_bool = ~df[col].isin(
                    [
                        True,
                        False,
                        1,
                        0,
                        "true",
                        "false",
                        "True",
                        "False",
                        pd.NA,
                        None,
                        "Ja",
                        "Nee",
                    ]
                )
                if invalid_bool.any():
                    validation_errors["warnings"].append(
                        {
                            "message": f"Ongeldige boolean waarden in kolom '{col}'",
                            "details": f"{invalid_bool.sum()} rijen hebben ongeldige waarden",
                        }
                    )

            elif specs["type"] == "DATE":
                try:
                    dates = pd.to_datetime(df[col], errors="raise")
                    if "date_format" in specs and specs["date_format"] == "yyyy":
                        invalid_years = (
                            ~dates.dt.strftime("%Y").astype(str).str.match(r"^\d{4}$")
                        )
                        if invalid_years.any():
                            validation_errors["warnings"].append(
                                {
                                    "message": f"Ongeldige jaarnotatie in kolom '{col}'",
                                    "details": f"{invalid_years.sum()} rijen hebben geen geldig jaartal (YYYY)",
                                }
                            )
                except Exception:
                    validation_errors["warnings"].append(
                        {
                            "message": f"Ongeldige datumwaarden in kolom '{col}'",
                            "details": "Kolom bevat ongeldige datumformaten",
                        }
                    )

            # Check allowed values if specified
            if "allowed_values" in specs:
                # Ensure we're working with a pandas Series
                col_series = df[col].astype(str)
                invalid_values = ~col_series.isin(specs["allowed_values"])
                invalid_rows = col_series[invalid_values]
                if invalid_values.any():
                    invalid_values_list = [
                        str(val) if pd.notna(val) else "Leeg"
                        for val in invalid_rows.unique()
                    ]
                    allowed_values = ", ".join(specs["allowed_values"])
                    found_values = ", ".join(invalid_values_list)
                    validation_errors["critical"].append({
                        "message": f"Ongeldige waarden in kolom '{col}'",
                        "details": (
                            f"Gevonden ongeldige waarden: [{found_values}]. "
                            f"Toegestane waarden zijn: [{allowed_values}]"
                        ),
                    })

    return validation_errors
