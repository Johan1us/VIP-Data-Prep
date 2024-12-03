from hashlib import sha256
import pandas as pd
import requests
import streamlit as st
from typing import Any, Dict, List, Union

from src.api_client import LuxsAcceptClient
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()


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


def check_password() -> bool:
    """Returns `True` if the user had the correct password."""

    def password_entered() -> None:
        """Checks whether a password entered by the user is correct."""
        if (
            sha256(st.session_state["password"].encode()).hexdigest()
            == st.secrets["password"]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Wachtwoord", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Wachtwoord", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Wachtwoord incorrect")
        return False
    else:
        return True


# Custom CSS for minimal, Outlook-like design
st.markdown(
    """
<style>
    /* Main container */
    .main {
        background-color: #ffffff;
    }

    /* Headers */
    h1, h2, h3 {
        color: #2b579a;
        font-weight: 500;
    }

    /* Buttons */
    .stButton>button {
        background-color: #ffffff;
        color: #2b579a;
        border: 1px solid #2b579a;
        padding: 4px 12px;
        border-radius: 2px;
        font-weight: 400;
        margin: 0;
    }
    .stButton>button:hover {
        background-color: #f0f2f6;
        color: #2b579a;
        border: 1px solid #2b579a;
    }

    /* Text inputs */
    .stTextInput>div>div>input {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 4px 12px;
        border-radius: 2px;
    }

    /* File uploader */
    .stFileUploader>div {
        padding: 12px;
        border: 1px solid #e0e0e0;
        border-radius: 2px;
    }

    /* Success/Info/Error messages */
    .stSuccess, .stInfo, .stError {
        padding: 8px 16px;
        border-radius: 2px;
        border: none;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 2px;
    }

    /* Remove default Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom container for content sections */
    .content-section {
        padding: 1.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 2px;
        margin: 1rem 0;
    }

    /* Dataframe styling */
    .dataframe {
        border: none !important;
    }
    .dataframe td, .dataframe th {
        border: 1px solid #e0e0e0 !important;
        padding: 8px !important;
    }

    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem;
        color: #2b579a;
    }
</style>
""",
    unsafe_allow_html=True,
)


def create_header() -> None:
    """Create the header section of the Streamlit app."""
    header_container = st.container()
    with header_container:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.title("VIP Data Voorbereiding")
        with col2:
            if st.button("⚙️"):
                st.session_state.show_settings = not st.session_state.get(
                    "show_settings", False
                )


def main() -> None:
    """Main function to run the Streamlit application."""
    # Initialize session state for settings
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False

    if not check_password():
        st.markdown(
            """
            <div style='padding: 2rem; max-width: 400px; margin: 0 auto;'>
                <h2 style='color: #2b579a; margin-bottom: 2rem;'>Login</h2>
            </div>
        """,
            unsafe_allow_html=True,
        )
        st.stop()

    create_header()

    # Settings panel (if enabled)
    if st.session_state.show_settings:
        with st.expander("Instellingen", expanded=True):
            st.write("Configuratie opties hier...")

    # Initialize the API client
    api_client = LuxsAcceptClient()

    # Add logging section with minimal design
    with st.expander("📋 Log", expanded=False):
        if "log_messages" not in st.session_state:
            st.session_state.log_messages = []

        for msg in st.session_state.log_messages:
            st.write(msg)

    # API Authentication status
    try:
        if api_client.authenticate():
            st.session_state.log_messages.append(
                f"✓ {pd.Timestamp.now().strftime('%H:%M:%S')} - API Authenticatie succesvol"
            )
        else:
            st.error("API Authenticatie mislukt")
    except Exception as e:
        st.error(f"API Authenticatie fout: {str(e)}")

    # File upload section
    st.markdown("### Data Upload")
    uploaded_file = st.file_uploader(
        "Kies een CSV-bestand",
        type="csv",
        help="Upload een CSV-bestand om uw data te bekijken en voor te bereiden",
    )

    if uploaded_file is not None:
        try:
            # Read and process the CSV file
            df = pd.read_csv(uploaded_file, sep=";", encoding="utf-8")

            # Data overview
            st.markdown("### Data Overzicht")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Aantal rijen", df.shape[0])
            with col2:
                st.metric("Aantal kolommen", df.shape[1])

            # Show preview in a clean table
            st.markdown("#### Voorbeeld van uw data")
            st.dataframe(df.head(), use_container_width=True)

            # Validation
            st.markdown("### Validatie Resultaten")
            validation_errors = validate_csv_structure(df)

            if validation_errors["critical"]:
                st.error("Kritieke problemen die opgelost moeten worden:")
                for error in validation_errors["critical"]:
                    if isinstance(error, dict):
                        st.markdown(f"- **{error['message']}**")
                        if isinstance(error["details"], list):
                            st.markdown("  - " + "\n  - ".join(error["details"]))
                        else:
                            st.markdown(f"  - {error['details']}")
                    else:
                        st.markdown(f"- {error}")
                st.info(
                    "📝 Tip: Los deze kritieke problemen op in uw data en upload het bestand opnieuw."
                )
            else:
                if validation_errors["warnings"]:
                    st.warning("Waarschuwingen die aandacht nodig hebben:")
                    for warning in validation_errors["warnings"]:
                        if isinstance(warning, dict):
                            st.markdown(f"- **{warning['message']}**")
                            if isinstance(warning["details"], list):
                                st.markdown("  - " + "\n  - ".join(warning["details"]))
                            else:
                                st.markdown(f"  - {warning['details']}")
                        else:
                            st.markdown(f"- {warning}")
                    st.info(
                        "📝 Tip: U kunt doorgaan met uploaden, maar het wordt aangeraden deze waarschuwingen te controleren."
                    )
                else:
                    st.success(
                        "✅ Uw CSV-bestand heeft alle validatiecontroles doorstaan!"
                    )

                # Alleen JSON preview en upload knop tonen als er geen kritieke fouten zijn
                # Convert DataFrame to JSON
                json_data = df.to_json(orient="records", force_ascii=False)

                # Display JSON preview
                st.subheader("🔄 JSON Preview")
                with st.expander("Bekijk JSON data"):
                    st.json(json_data)

                # Add upload button
                if st.button("📤 Upload naar API"):
                    try:
                        with st.spinner("Bezig met uploaden..."):
                            # Prepare the payload
                            payload = prepare_api_payload(df)
                            st.session_state.log_messages.append(
                                f"🕐 {pd.Timestamp.now().strftime('%H:%M:%S')} - Start upload van {len(payload)} objecten"
                            )

                            response = api_client.make_request(
                                "v1/objects", method="POST", data=payload
                            )

                            if response.status_code == 200:
                                # Process response
                                result = response.json()
                                success_count = sum(
                                    1 for obj in result if obj["success"]
                                )
                                created_count = sum(
                                    1
                                    for obj in result
                                    if obj["success"] and obj["isCreation"]
                                )
                                updated_count = sum(
                                    1
                                    for obj in result
                                    if obj["success"] and not obj["isCreation"]
                                )

                                st.session_state.log_messages.append(
                                    f"✅ {pd.Timestamp.now().strftime('%H:%M:%S')} - Upload succesvol: {success_count} objecten verwerkt ({created_count} nieuw, {updated_count} bijgewerkt)"
                                )
                                st.success(
                                    f"✅ Data succesvol verwerkt: {success_count} objecten ({created_count} nieuw, {updated_count} bijgewerkt)"
                                )

                                # Show detailed results in expander
                                with st.expander("Details van de upload"):
                                    for obj in result:
                                        status = "✅" if obj["success"] else "❌"
                                        action = (
                                            "Aangemaakt"
                                            if obj["isCreation"]
                                            else "Bijgewerkt"
                                        )
                                        st.write(
                                            f"{status} {obj['objectType']} {obj['identifier']}: {action} - {obj['message']}"
                                        )

                    except requests.exceptions.ConnectionError:
                        st.session_state.log_messages.append(
                            f"❌ {pd.Timestamp.now().strftime('%H:%M:%S')} - Verbindingsfout"
                        )
                        st.error(
                            "❌ Kon geen verbinding maken met de API. Controleer uw internetverbinding."
                        )
                    except Exception as e:
                        st.session_state.log_messages.append(
                            f"❌ {pd.Timestamp.now().strftime('%H:%M:%S')} - Fout: {str(e)}"
                        )
                        st.error(f"❌ API Upload fout: {str(e)}")

        except Exception as e:
            st.error(f"Fout: {str(e)}")
            st.write("Zorg ervoor dat u een geldig CSV-bestand heeft geüpload.")


if __name__ == "__main__":
    main()
