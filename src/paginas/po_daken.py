import streamlit as st
import logging
import pandas as pd
from services.po_daken_service import PODakenService
from configuratie.config_po_daken import COLUMNS_MAPPING_DAKEN

logger = logging.getLogger(__name__)


def render(luxs_api_client):
    """
    Render de 'PO Daken' pagina.

    Deze pagina bestaat uit twee delen (tabbladen):
    1. Downloaden van bestaande data (Excel-bestand met PO Daken gegevens).
    2. Uploaden van geüpdatete data (Excel-bestand) om wijzigingen terug te sturen naar de API.

    Args:
        luxs_api_client: De API client die gebruikt wordt om data op te halen en te versturen.
    """
    st.title("PO Daken")

    # Get the selected env from the session state
    selected_env = st.session_state.environment
    logger.debug(f"Selected environment: {selected_env}")

    # try:
    # 1. Initialiseer de service om data over PO Daken te beheren.
    po_daken_service = PODakenService(luxs_api_client)

    print(po_daken_service)
    logger.debug("PO Daken service succesvol geïnitialiseerd.")

    # 2. Maak twee tabbladen: een voor downloaden en een voor uploaden.
    tab_download, tab_upload = st.tabs(["Download Data", "Upload Updates"])

    # -------------------------------------
    # TAB 1: Download Data
    # -------------------------------------
    with tab_download:
        st.markdown("### 📥 Download PO Daken Dataset")

        # Als de gebruiker op de downloadknop klikt, voer dan het downloadproces uit.
        if st.button("Download PO Daken Dataset"):
            # Voor visuele feedback maken we een voortgangsbalk en statusberichten
            progress_bar = st.progress(0)
            status_text = st.empty()

            # try:
            # STAP 1: Authenticatie / voorwerk
            status_text.text("🔄 Authenticeren met de API...")
            progress_bar.progress(20)

            # STAP 2: Haal gebouwen op uit de API (of eventueel uit een lokaal JSON-bestand voor test)
            status_text.text("🏢 Ophalen van gebouwen...")
            progress_bar.progress(40)

            # dev: Flag om te testen met lokaal opgeslagen data in plaats van een echte API-call.
            dev = False
            if dev:
                # Lees testdata uit een lokaal JSON-bestand
                buildings = pd.read_json("src/buildings.json").to_dict('records')
            else:
                # Haal data op via de service
                buildings = po_daken_service.get_all_buildings()

            print(f"buildings: {len(buildings)}")


            # print de eerste 5 gebouwen
            logger.debug(f"Gebruikte kolommen: {COLUMNS_MAPPING_DAKEN}")
            logger.debug(f"Kolommen van gebouwen: {buildings[0].keys()}")
            logger.debug(f"Voorbeeld van gebouwen: {buildings[:2]}")

            # Controleer of er gebouwen zijn opgehaald
            if buildings:
                # STAP 3: Verwerk de data en pas kolomnamen aan volgens COLUMNS_MAPPING_DAKEN
                status_text.text("📊 Verwerken van data...")
                progress_bar.progress(60)

                # # Hernoem de kolommen op basis van COLUMNS_MAPPING_DAKEN
                # # buildings is een lijst van dictionaries (per gebouw)
                # buildings = [
                #     {COLUMNS_MAPPING_DAKEN.get(k, k): v for k, v in building.items()}
                #     for building in buildings
                # ]

                # STAP 4: Genereer een Excel-bestand van de opgehaalde data
                status_text.text("📝 Genereren van Excel bestand...")
                progress_bar.progress(80)

                excel_data = po_daken_service.export_to_excel(buildings)

                # Controleer of Excel succesvol is aangemaakt
                progress_bar.progress(100)
                if excel_data:
                    status_text.empty()
                    st.success("✅ PO Daken dataset succesvol gegenereerd!")

                    # Bied de gebruiker een downloadknop aan voor de Excel-file
                    st.download_button(
                        label="📥 Download Excel file",
                        data=excel_data,
                        file_name="PO_Daken_Dataset.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    # Kon geen Excel bestand genereren
                    status_text.empty()
                    st.error("❌ Er is een fout opgetreden bij het genereren van het Excel-bestand.")
            else:
                # Geen gebouwen gevonden
                status_text.empty()
                st.error("❌ Geen data beschikbaar om te exporteren.")

            # Verwijder voortgangsbalk
            progress_bar.empty()

            # except Exception as e:
            #     # Fout tijdens het downloadproces
            #     error_msg = f"❌ Er is een fout opgetreden bij het downloaden: {str(e)}"
            #     logger.error(error_msg)
            #     st.error(error_msg)
            #     progress_bar.empty()
            #     status_text.empty()

    # -------------------------------------
    # TAB 2: Upload Updates
    # -------------------------------------
    with tab_upload:
        st.markdown("### 📤 Upload bijgewerkte PO Daken Dataset")

        # Gebruiker kan hier een Excel-bestand uploaden met bijgewerkte data.
        uploaded_file = st.file_uploader("Selecteer een Excel bestand", type=['xlsx'])

        if uploaded_file is not None:
            try:


                # Lees het geüploade Excel-bestand in
                df = pd.read_excel(uploaded_file)
                logger.debug(f"Eerst regels df {df.head()}")

                # Toon een voorbeeld van de eerste rijen om te valideren of het bestand correct is
                st.write("Voorbeeld van de geüploade data:")
                st.dataframe(df.head())

                # Knop om de data naar de API te sturen
                if st.button("Valideren en Uploaden"):
                    with st.spinner("Valideren en uploaden van data..."):
                        try:
                            # Probeer de data te verwerken via de service
                            logger.debug("Valideer en Upload data"                             )
                            success = po_daken_service.process_uploaded_data(df)
                            if success:
                                st.success("✅ Data succesvol geüpload!")
                            else:
                                st.error("❌ Fout bij het uploaden van data.")
                        except Exception as e:
                            foutmelding = f"❌ Fout bij het verwerken van data: {str(e)}"
                            st.error(foutmelding)
                            logger.error(f"Fout bij geüploade data verwerken: {str(e)}")

            except Exception as e:
                # Fout bij het inlezen van het geüploade bestand
                foutmelding = f"❌ Fout bij het inlezen van het bestand: {str(e)}"
                st.error(foutmelding)
                logger.error(f"Fout bij inlezen geüpload bestand: {str(e)}")

    # except Exception as e:
    #     # Als de service niet kon worden geïnitialiseerd
    #     error_msg = f"❌ Er is een fout opgetreden bij het initialiseren van de PO Daken service: {str(e)}"
    #     logger.error(error_msg)
    #     st.error(error_msg)


def handle_upload(uploaded_file, po_daken_service):
    """
    Verwerk het geüploade bestand met extra functionaliteit, zoals voortgangsbalk en stopmogelijkheid.

    Args:
        uploaded_file (BytesIO): Het geüploade Excel-bestand.
        po_daken_service (PODakenService): Service om de data mee te verwerken.
    """
    try:
        # Lees het Excel-bestand in een DataFrame
        df = pd.read_excel(uploaded_file)

        # Toon voorbeelddata aan de gebruiker
        st.write("Voorbeeld van geüploade data:")
        st.dataframe(df.head())

        # Gebruik sessie-state om te bepalen of er een stop-signaal is gegeven door de gebruiker
        if 'stop_upload' not in st.session_state:
            st.session_state.stop_upload = False

        # Twee knoppen: start en stop
        col1, col2 = st.columns(2)

        with col1:
            start_upload = st.button("Start Upload")

        with col2:
            if st.button("Stop Upload"):
                st.session_state.stop_upload = True
                st.warning("⚠️ Stop-signaal verzonden. Wacht totdat de huidige batch klaar is...")

        # Als de gebruiker op "Start Upload" heeft geklikt
        if start_upload:
            # Reset eerder stop-signaal
            st.session_state.stop_upload = False

            # Maak een voortgangsbalk en velden voor status en statistieken
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_container = st.empty()

            try:
                # Verwerk in batches met statusupdates
                with st.spinner("Bezig met valideren en uploaden..."):
                    success = process_upload_with_status(
                        df,
                        po_daken_service,
                        progress_bar,
                        status_text,
                        metrics_container
                    )

                    if success:
                        st.success("✅ Data succesvol geüpload!")
                    else:
                        st.error("❌ Upload proces afgebroken of mislukt.")

            except Exception as e:
                logger.error(f"Upload fout: {str(e)}")
                st.error(f"❌ Fout tijdens het upload proces: {str(e)}")

            finally:
                progress_bar.empty()
                status_text.empty()

    except Exception as e:
        logger.error(f"Upload fout: {str(e)}")
        st.error(f"❌ Fout bij verwerken van bestand: {str(e)}")


def process_upload_with_status(df, po_daken_service, progress_bar, status_text, metrics_container):
    """
    Verwerk het uploaden van data in batches met voortgangsinformatie.

    Stappen:
    - Verdeel de data in batches (van bijv. 100 records).
    - Verwerk elke batch via een (fictieve) methode 'process_batch' van de PODakenService.
    - Update voortgang, toon statistieken en controleer of de gebruiker een stop-signaal heeft gegeven.

    Args:
        df (pd.DataFrame): De te uploaden data.
        po_daken_service (PODakenService): De service die batches kan verwerken.
        progress_bar (streamlit.progress): Widget om voortgang te tonen.
        status_text (streamlit.empty): Widget om statusberichten in te tonen.
        metrics_container (streamlit.empty): Widget om statistieken te tonen (aantal verwerkt, succesvol, mislukt).

    Returns:
        bool: True als succesvol (er is minstens één batch goed gegaan), False als gestopt of mislukt.
    """
    try:
        # Converteer DataFrame naar lijst van dictionaries.
        buildings_data = df.to_dict('records')
        totaal = len(buildings_data)

        # Variabelen voor tellingen
        verwerkt = 0
        succesvol = 0
        mislukt = 0

        # Bepaal batch-grootte
        batch_grootte = 100

        # Verwerk in batches
        for i in range(0, totaal, batch_grootte):
            # Check of de gebruiker wil stoppen
            if st.session_state.stop_upload:
                status_text.text("⚠️ Upload gestopt door gebruiker")
                return False

            # Pak de huidige batch
            batch = buildings_data[i:i + min(batch_grootte, totaal - i)]
            status_text.text(f"🔄 Verwerken van records {i + 1} tot {i + len(batch)} van {totaal}")

            try:
                # Fictieve methode 'process_batch' in de service om de batch te verwerken.
                batch_success = po_daken_service.process_batch(batch)

                if batch_success:
                    succesvol += len(batch)
                else:
                    mislukt += len(batch)

            except Exception as e:
                # Fout bij verwerken van deze batch
                logger.error(f"Batch fout: {str(e)}")
                mislukt += len(batch)

            # Update tellingen
            verwerkt = i + len(batch)
            voortgang = int((verwerkt / totaal) * 100)
            progress_bar.progress(voortgang)

            # Toon bijgewerkte statistieken
            metrics_container.markdown(f"""
                ### Status
                - Verwerkt: {verwerkt}/{totaal}
                - Succesvol: {succesvol}
                - Mislukt: {mislukt}
            """)

        # Als alle batches zijn verwerkt, kijk of er iets gelukt is.
        return succesvol > 0

    except Exception as e:
        logger.error(f"Verwerkingsfout: {str(e)}")
        status_text.text(f"❌ Fout tijdens verwerking: {str(e)}")
        return False
