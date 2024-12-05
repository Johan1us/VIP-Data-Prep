import streamlit as st
from components.header import create_header
from _pages import home, po_daken
from utils.logging_config import setup_logging
import hashlib
import logging

# Configuratie van de logging
logging.basicConfig(
    level=logging.DEBUG,  # Logniveau instellen op DEBUG voor gedetailleerde informatie
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Formaat van logberichten
    handlers=[
        logging.StreamHandler(),  # Log naar de console
        logging.FileHandler('app.log')  # Log naar het bestand 'app.log'
    ]
)

logger = logging.getLogger(__name__)  # Logger voor deze module

setup_logging()  # Extra logginginstellingen initialiseren

def check_password() -> bool:
    """
    Controleer of de gebruiker het juiste wachtwoord heeft ingevoerd.

    Returns:
        bool: True als het wachtwoord correct is, anders False.
    """
    # Controleer of de status van het wachtwoord al is opgeslagen in de sessie
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False  # Standaard instellen op False

    if st.session_state.password_correct:
        return True  # Toegang verlenen als het wachtwoord al correct is

    # Vraag de gebruiker om het wachtwoord in te voeren
    wachtwoord = st.text_input("Wachtwoord", type="password")
    if wachtwoord:
        # Vergelijk de SHA-256 hash van het ingevoerde wachtwoord met de opgeslagen hash
        if hashlib.sha256(wachtwoord.encode()).hexdigest() == st.secrets["password"]:
            st.session_state.password_correct = True  # Markeer als correct
            st.rerun()  # Herlaad de toepassing
            return True
        else:
            st.error("❌ Onjuist wachtwoord")  # Toon foutmelding
            return False
    return False  # Geen wachtwoord ingevoerd

def load_css():
    """
    Laad aangepaste CSS-stijlen voor de toepassing.
    """
    css_bestand = "../static/css/style.css"  # Pad naar het CSS-bestand
    with open(css_bestand) as f:
        # Injecteer de CSS in de Streamlit applicatie
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def initialize_session_state():
    """
    Initialiseert de nodige sessiestatusvariabelen.
    """
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = True  # Standaard instellingen verbergen
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []  # Lijst voor logberichten
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"  # Standaardpagina instellen

def main() -> None:
    """
    Hoofdfunctie die de Streamlit toepassing uitvoert.
    """
    load_css()  # Laad de aangepaste CSS
    initialize_session_state()  # Initialiseer sessiestatus

    if not check_password():
        # Toon alleen het inlogscherm als het wachtwoord niet correct is
        st.markdown(
            """
            <div style='padding: 2rem; max-width: 400px; margin: 0 auto;'>
                <h2 style='color: #2b579a; margin-bottom: 2rem;'>Inloggen</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()  # Stop verdere uitvoering totdat het wachtwoord correct is

    create_header()  # Voeg de header toe aan de applicatie

    # Navigatiebalk in de zijbalk
    st.sidebar.title("Navigatie")
    paginas = {
        "Home": ("🏠", home.render),  # Paginanaam: (Icon, render functie)
        "PO Daken": ("🏢", po_daken.render)
    }

    # Laat de gebruiker een pagina selecteren
    geselecteerde_pagina = st.sidebar.radio(
        "Ga naar",
        list(paginas.keys()),
        format_func=lambda x: f"{paginas[x][0]} {x}"  # Formatteer met icoon
    )

    st.session_state.current_page = geselecteerde_pagina  # Sla de geselecteerde pagina op

    # Render de geselecteerde pagina
    paginas[geselecteerde_pagina][1]()  # Roep de render functie aan

    with st.expander("📋 Log", expanded=False):
        for msg in st.session_state.log_messages:
            st.write(msg)  # Toon elk logbericht

if __name__ == "__main__":
    main()  # Start de applicatie wanneer het script direct wordt uitgevoerd
