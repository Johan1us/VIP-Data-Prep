import os
import pandas as pd
import streamlit as st
from hashlib import sha256
from typing import Any, Dict, List, Union

# Import refactored components and services
from src.components.header import create_header
from src.components.validation import validate_csv_structure
from src.services.api import prepare_api_payload, get_api_client

# Setup logging
from src.utils.logging_config import setup_logging
setup_logging()

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

def load_css():
    css_file_path = os.path.join(os.path.dirname(__file__), 'static/css/style.css')
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def initialize_session_state():
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []

def display_login_prompt():
    st.markdown(
        """
        <div style='padding: 2rem; max-width: 400px; margin: 0 auto;'>
            <h2 style='color: #2b579a; margin-bottom: 2rem;'>Login</h2>
        </div>
    """,
        unsafe_allow_html=True,
    )

def display_settings_panel():
    if st.session_state.show_settings:
        with st.expander("Instellingen", expanded=True):
            st.write("Configuratie opties hier...")

def display_log_section():
    with st.expander("📋 Log", expanded=False):
        for msg in st.session_state.log_messages:
            st.write(msg)

def authenticate_api(api_client):
    try:
        if api_client.authenticate():
            st.session_state.log_messages.append(
                f"✓ {pd.Timestamp.now().strftime('%H:%M:%S')} - API Authenticatie succesvol"
            )
            return True
        else:
            st.error("API Authenticatie mislukt")
            return False
    except Exception as e:
        st.error(f"API Authenticatie fout: {str(e)}")
        return False

def handle_file_upload(api_client):
    st.markdown("### Data Upload")
    uploaded_file = st.file_uploader(
        "Kies een CSV-bestand",
        type="csv",
        help="Upload een CSV-bestand om uw data te bekijken en voor te bereiden",
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, sep=";", encoding="utf-8")
            display_data_overview(df)
            validation_errors = validate_csv_structure(df)
            handle_validation_results(validation_errors, df, api_client)
        except Exception as e:
            st.error(f"Fout: {str(e)}")
            st.write("Zorg ervoor dat u een geldig CSV-bestand heeft geüpload.")

def display_data_overview(df):
    st.markdown("### Data Overzicht")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Aantal rijen", df.shape[0])
    with col2:
        st.metric("Aantal kolommen", df.shape[1])
    st.markdown("#### Voorbeeld van uw data")
    st.dataframe(df.head(), use_container_width=True)

def handle_validation_results(validation_errors, df, api_client):
    st.markdown("### Validatie Resultaten")
    if validation_errors["critical"]:
        display_critical_errors(validation_errors["critical"])
    else:
        if validation_errors["warnings"]:
            display_warnings(validation_errors["warnings"])
        else:
            st.success("✅ Uw CSV-bestand heeft alle validatiecontroles doorstaan!")
        display_json_preview(df)
        if st.button("📤 Upload naar API"):
            upload_to_api(df, api_client)

def display_critical_errors(errors):
    st.error("Kritieke problemen die opgelost moeten worden:")
    for error in errors:
        if isinstance(error, dict):
            st.markdown(f"- **{error['message']}**")
            if isinstance(error["details"], list):
                st.markdown("  - " + "\n  - ".join(error["details"]))
            else:
                st.markdown(f"  - {error['details']}")
        else:
            st.markdown(f"- {error}")
    st.info("📝 Tip: Los deze kritieke problemen op in uw data en upload het bestand opnieuw.")

def display_warnings(warnings):
    st.warning("Waarschuwingen die aandacht nodig hebben:")
    for warning in warnings:
        if isinstance(warning, dict):
            st.markdown(f"- **{warning['message']}**")
            if isinstance(warning["details"], list):
                st.markdown("  - " + "\n  - ".join(warning["details"]))
            else:
                st.markdown(f"  - {warning['details']}")
        else:
            st.markdown(f"- {warning}")
    st.info("📝 Tip: U kunt doorgaan met uploaden, maar het wordt aangeraden deze waarschuwingen te controleren.")

def display_json_preview(df):
    json_data = df.to_json(orient="records", force_ascii=False)
    st.subheader("🔄 JSON Preview")
    with st.expander("Bekijk JSON data"):
        st.json(json_data)

def upload_to_api(df, api_client):
    try:
        with st.spinner("Bezig met uploaden..."):
            payload = prepare_api_payload(df)
            st.session_state.log_messages.append(
                f"🕐 {pd.Timestamp.now().strftime('%H:%M:%S')} - Start upload van {len(payload)} objecten"
            )
            response = api_client.make_request("v1/objects", method="POST", data=payload)
            process_upload_response(response)
    except requests.exceptions.ConnectionError:
        st.session_state.log_messages.append(
            f"❌ {pd.Timestamp.now().strftime('%H:%M:%S')} - Verbindingsfout"
        )
        st.error("❌ Kon geen verbinding maken met de API. Controleer uw internetverbinding.")
    except Exception as e:
        st.session_state.log_messages.append(
            f"❌ {pd.Timestamp.now().strftime('%H:%M:%S')} - Fout: {str(e)}"
        )
        st.error(f"❌ API Upload fout: {str(e)}")

def process_upload_response(response):
    if response.status_code == 200:
        result = response.json()
        success_count = sum(1 for obj in result if obj["success"])
        created_count = sum(1 for obj in result if obj["success"] and obj["isCreation"])
        updated_count = sum(1 for obj in result if obj["success"] and not obj["isCreation"])
        st.session_state.log_messages.append(
            f"✅ {pd.Timestamp.now().strftime('%H:%M:%S')} - Upload succesvol: {success_count} objecten verwerkt ({created_count} nieuw, {updated_count} bijgewerkt)"
        )
        st.success(f"✅ Data succesvol verwerkt: {success_count} objecten ({created_count} nieuw, {updated_count} bijgewerkt)")
        with st.expander("Details van de upload"):
            for obj in result:
                status = "✅" if obj["success"] else "❌"
                action = "Aangemaakt" if obj["isCreation"] else "Bijgewerkt"
                st.write(f"{status} {obj['objectType']} {obj['identifier']}: {action} - {obj['message']}")

def main() -> None:
    """Main function to run the Streamlit application."""
    load_css()
    initialize_session_state()

    if not check_password():
        display_login_prompt()
        st.stop()

    create_header()
    display_settings_panel()
    api_client = get_api_client()
    display_log_section()

    if not authenticate_api(api_client):
        return

    handle_file_upload(api_client)

if __name__ == "__main__":
    main()
