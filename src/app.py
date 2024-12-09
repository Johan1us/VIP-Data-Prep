import streamlit as st
from components.header import create_header
from paginas import home, po_daken
from utils.logging_config import setup_logging
import hashlib
import logging
import sys
from api.api_client import LuxsClient

# ----------------------------------------
# Log-instellingen configureren
# ----------------------------------------
# Forceer UTF-8 encoding voor logging output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Use stdout with UTF-8 encoding
        logging.FileHandler('app.log', encoding='utf-8')  # Specify UTF-8 encoding for file
    ]
)

logger = logging.getLogger(__name__)

# Voer extra loggingconfiguratie uit via een aparte functie
setup_logging()


def check_password() -> bool:
    """
    Controleer of de gebruiker het juiste wachtwoord heeft ingevoerd.
    Het wachtwoord is opgeslagen als een SHA-256 hash in st.secrets.

    Returns:
        bool: True als het wachtwoord correct is, False als het fout is of niet is ingevoerd.
    """
    # Controleer of we al weten of het wachtwoord correct is
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    # Als het wachtwoord al eens correct is ingevoerd, direct True teruggeven
    if st.session_state.password_correct:
        return True

    # Gebruiker om een wachtwoord vragen
    wachtwoord = st.text_input("Wachtwoord", type="password")

    # Als de gebruiker iets heeft ingevoerd, controleer dan de hash
    if wachtwoord:
        # Vergelijk de SHA-256 hash van het ingevoerde wachtwoord met de hash uit st.secrets
        ingevoerde_hash = hashlib.sha256(wachtwoord.encode()).hexdigest()
        if ingevoerde_hash == st.secrets["password"]:
            # Als het klopt, sla dit op en herlaad de pagina
            st.session_state.password_correct = True
            st.rerun()
            return True
        else:
            # Als het niet klopt, laat een foutmelding zien
            st.error("❌ Onjuist wachtwoord")
            return False

    # Geen wachtwoord ingevoerd, dus nog geen toegang
    return False


def load_css():
    """
    Laad aangepaste CSS-stijlen om het uiterlijk van de Streamlit-app aan te passen.
    """
    css_bestand = "src/static/css/style.css"
    with open(css_bestand) as f:
        # Met 'unsafe_allow_html=True' kunnen we zelf HTML/CSS injecteren.
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def initialize_session_state():
    """
    Initialiseert alle benodigde variabelen in de Streamlit sessie.
    Hierdoor kunnen we gegevens bewaren tijdens navigatie zonder dat deze verloren gaan.
    """
    if "environment" not in st.session_state:
        st.session_state.environment = "Acceptatie"  # Default waarde

    if "show_settings" not in st.session_state:
        # Geeft aan of we een instellingenpaneel laten zien (True/False).
        st.session_state.show_settings = True

    if "log_messages" not in st.session_state:
        # Hierin kunnen we logberichten opslaan die we in de UI willen tonen.
        st.session_state.log_messages = []

    if "current_page" not in st.session_state:
        # Huidige geopende pagina. Standaard naar "Home".
        st.session_state.current_page = "Home"

    if "api_client" not in st.session_state:
        # Maak één keer een API-client object aan en bewaar het.
        st.session_state.api_client = LuxsClient(environment=st.session_state.environment)


def main() -> None:
    """
    Hoofdfunctie van de Streamlit-app.
    Deze functie regelt de totale flow: CSS laden, sessie init,
    inloggen, header tonen, navigatie en het tonen van de geselecteerde pagina.
    """
    # 1. Laad de aangepaste CSS
    load_css()

    # 2. Initialiseert alle sessievariabelen die we nodig hebben
    initialize_session_state()

    # 3. Controleer of de gebruiker is ingelogd
    # if not check_password():
    #     # Zo niet, toon dan alleen een inlogscherm
    #     st.markdown(
    #         """
    #         <div style='padding: 2rem; max-width: 400px; margin: 0 auto;'>
    #             <h2 style='color: #2b579a; margin-bottom: 2rem;'>Inloggen</h2>
    #         </div>
    #         """,
    #         unsafe_allow_html=True,
    #     )
    #     # Stop hier; pas als het wachtwoord correct is, gaat de rest door
    #     st.stop()

    # 4. Toon de header bovenaan de pagina met de geselecteerde omgeving
    create_header(st.session_state.environment)

    # 5. Zijbalk navigatie: hiermee kan de gebruiker van pagina wisselen
    st.sidebar.title("Navigatie")
    paginas = {
        "Home": ("🏠", lambda: home.render()),
        "PO Daken": ("🏢", lambda: po_daken.render(st.session_state.api_client))
    }

    # 6. Toon een radioknop menu in de zijbalk voor het kiezen van de pagina
    geselecteerde_pagina = st.sidebar.radio(
        "Ga naar",
        list(paginas.keys()),
        format_func=lambda x: f"{paginas[x][0]} {x}"  # Voeg een icoontje toe aan de paginanaam
    )

    # Sla de huidige pagina op in de sessie
    st.session_state.current_page = geselecteerde_pagina

    # 7. Render de inhoud van de geselecteerde pagina
    paginas[geselecteerde_pagina][1]()

    # 8. Onderin, onder een 'expander', tonen we de logberichten.
    with st.expander("📋 Log", expanded=False):
        for msg in st.session_state.log_messages:
            st.write(msg)


# Voer de main functie uit als dit bestand direct wordt gestart.
if __name__ == "__main__":
    main()
