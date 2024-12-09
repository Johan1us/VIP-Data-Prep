import streamlit as st
from services.connection_test_service import ConnectionTestService

def render():
    """
    Deze functie toont de 'Home' pagina van de applicatie.
    Hier kun je algemene informatie weergeven of een introductie geven
    tot je applicatie.
    """
    # Toon de titel van de pagina
    st.title("Home")

    # Toon een korte welkomstboodschap
    st.write("Welkom op de hoofdpagina van de applicatie!")

    # Maak een instantie van de ConnectionTestService
    connection_service = ConnectionTestService()

    # Voeg een radio button toe om de omgeving te kiezen
    environment = st.radio(
        "Kies de omgeving om te testen:",
        ("Acceptatie", "Productie")
    )

    # Update de omgeving in session state wanneer deze verandert
    if environment != st.session_state.environment:
        st.session_state.environment = environment
        st.rerun()  # Herlaad de pagina om de header bij te werken

    # Maak twee kolommen voor de test knoppen
    col1, col2 = st.columns(2)

    # Test Acceptatie knop
    with col1:
        if st.button("Test Token Acceptatie"):
            with st.spinner("Testen van token authenticatie voor acceptatie..."):

                    if connection_service.test_accept_token():
                        st.success("✅ Token authenticatie voor acceptatie succesvol!")
                    else:
                        st.error("❌ Token authenticatie voor acceptatie mislukt")

    # Test Productie knop
    with col2:
        if st.button("Test Token Productie"):
            with st.spinner("Testen van token authenticatie voor productie..."):

                    if connection_service.test_prod_token():
                        st.success("✅ Token authenticatie voor productie succesvol!")
                    else:
                        st.error("❌ Token authenticatie voor productie mislukt")
