import streamlit as st
import logging
import pandas as pd
from services.po_daken_service import PODakenService

logger = logging.getLogger(__name__)


def render():
    """
    Deze functie rendert de PO Daken pagina met Streamlit.
    De pagina is opgedeeld in twee tabbladen:
    1. Downloaden van bestaande data (Excel bestand)
    2. Uploaden van geüpdatete data (Excel bestand) om deze in de API te verwerken
    """
    st.title("PO Daken")

    try:
        # 1. Initialiseer de service voor PO Daken.
        po_daken_service = PODakenService()

        # 2. Maak twee tabbladen aan: "Download Data" en "Upload Updates"
        tab1, tab2 = st.tabs(["Download Data", "Upload Updates"])

        # --- Download Tab ---
        with tab1:
            st.markdown("### 📥 Download PO Daken Dataset")

            # Als de gebruiker op de download-knop klikt
            if st.button("Download PO Daken Dataset"):
                # Toon een voortgangsbalk en statustekst
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    # Update status om aan te geven dat we aan het authenticeren zijn
                    status_text.text("🔄 Authenticeren met de API...")
                    progress_bar.progress(20)

                    # Haal gebouwen op via de service
                    status_text.text("🏢 Ophalen van gebouwen...")
                    progress_bar.progress(40)
                    buildings = po_daken_service.get_all_buildings()

                    if buildings:
                        # Verwerk gebouwen in Excel-bestand
                        status_text.text("📊 Verwerken van data...")
                        progress_bar.progress(60)

                        # Maak een Excel-bestand aan
                        status_text.text("📝 Genereren van Excel bestand...")
                        progress_bar.progress(80)
                        excel_data = po_daken_service.export_to_excel(buildings)

                        # Als het gelukt is
                        progress_bar.progress(100)
                        if excel_data:
                            status_text.empty()  # Clear de status tekst
                            st.success("✅ PO Daken dataset succesvol gegenereerd!")

                            # Bied een download knop voor het Excel-bestand
                            st.download_button(
                                label="📥 Download Excel file",
                                data=excel_data,
                                file_name="PO_Daken_Dataset.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            # Als het niet gelukt is om Excel te genereren
                            status_text.empty()
                            st.error("❌ Er is een fout opgetreden bij het genereren van het bestand.")
                    else:
                        # Geen gebouwen gevonden
                        status_text.empty()
                        st.error("❌ Geen data beschikbaar om te exporteren.")

                    # Ruim voortgangsbalk op
                    progress_bar.empty()

                except Exception as e:
                    # Log en toon de fout
                    error_msg = f"❌ Er is een fout opgetreden: {str(e)}"
                    logger.error(error_msg)
                    st.error(error_msg)
                    progress_bar.empty()
                    status_text.empty()

        # --- Upload Tab ---
        with tab2:
            st.markdown("### 📤 Upload bijgewerkte PO Daken Dataset")

            # Voeg een upload-veld toe om een Excel-bestand te kiezen
            uploaded_file = st.file_uploader("Selecteer een Excel bestand", type=['xlsx'])

            if uploaded_file is not None:
                try:
                    # Lees het geüploade Excel bestand in een DataFrame
                    df = pd.read_excel(uploaded_file)

                    # Toon een voorbeeld van de eerste rijen uit de dataset
                    st.write("Voorbeeld van de geüploade data:")
                    st.dataframe(df.head())

                    # Knop om de data te valideren en te uploaden
                    if st.button("Valideren en Uploaden"):
                        with st.spinner("Valideren en uploaden van data..."):
                            try:
                                # Verwerk en upload de data via de service
                                success = po_daken_service.process_uploaded_data(df)
                                if success:
                                    st.success("✅ Data succesvol geüpload!")
                                else:
                                    st.error("❌ Fout bij het uploaden van data")
                            except Exception as e:
                                st.error(f"❌ Fout bij het verwerken van data: {str(e)}")
                                logger.error(f"Fout bij het verwerken van geüploade data: {str(e)}")

                except Exception as e:
                    st.error(f"❌ Fout bij het inlezen van het bestand: {str(e)}")
                    logger.error(f"Fout bij het inlezen van geüpload bestand: {str(e)}")

    except Exception as e:
        # Als initialisatie van de service niet lukt
        error_msg = f"❌ Er is een fout opgetreden bij het initialiseren van de service: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)


def handle_upload(uploaded_file, po_daken_service):
    """
    Verwerk een geüpload bestand met extra functionaliteit:
    - Tonen van voortgang
    - Mogelijkheid om het upload-proces te stoppen

    Args:
        uploaded_file (BytesIO): Het geüploade Excel bestand
        po_daken_service (PODakenService): De service om data mee te verwerken
    """
    try:
        # Lees het Excel bestand
        df = pd.read_excel(uploaded_file)

        # Toon een voorbeeld van de data
        st.write("Voorbeeld van geüploade data:")
        st.dataframe(df.head())

        # Gebruik session_state om stop-signaal op te slaan
        if 'stop_upload' not in st.session_state:
            st.session_state.stop_upload = False

        # Maak twee kolommen voor start- en stop-knoppen
        col1, col2 = st.columns(2)

        # Start upload knop
        with col1:
            start_upload = st.button("Start Upload")

        # Stop upload knop
        with col2:
            if st.button("Stop Upload"):
                st.session_state.stop_upload = True
                st.warning("⚠️ Stop-signaal verzonden. Wacht tot de huidige batch klaar is...")

        # Als gebruiker op "Start Upload" klikt
        if start_upload:
            # Reset eventuele eerdere stop-signaal
            st.session_state.stop_upload = False

            # Maak een voortgangsbalk en statusvelden
            progress_bar = st.progress(0)
            status_text = st.empty()
            metrics_container = st.empty()

            try:
                # Start met valideren en uploaden in batches
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
                        st.error("❌ Upload proces afgebroken of mislukt")

            except Exception as e:
                logger.error(f"Upload fout: {str(e)}")
                st.error(f"❌ Fout tijdens upload proces: {str(e)}")

            finally:
                # Ruim voortgangsbalk en status op
                progress_bar.empty()
                status_text.empty()

    except Exception as e:
        logger.error(f"Upload fout: {str(e)}")
        st.error(f"❌ Fout bij verwerken van bestand: {str(e)}")


def process_upload_with_status(df, po_daken_service, progress_bar, status_text, metrics_container):
    """
    Verwerk de upload stap-voor-stap met statusupdates.

    Stappen:
    - Split de data op in batches van 100 records.
    - Verwerk elke batch via 'process_batch' (fictieve methode) in de service.
    - Toon voortgang en statistieken (hoeveel verwerkt, hoeveel succesvol, hoeveel mislukt).
    - Check steeds of de gebruiker op 'Stop Upload' heeft geklikt.

    Args:
        df (pd.DataFrame): DataFrame met te verwerken data
        po_daken_service (PODakenService): Service om batches mee te verwerken
        progress_bar (streamlit.progress): Voortgangsbalk om voortgang te tonen
        status_text (streamlit.empty): Tekstveld voor statusmeldingen
        metrics_container (streamlit.empty): Container om statistieken te tonen

    Returns:
        bool: True als er succesvol data is geüpload, False bij onderbreking of fout.
    """
    try:
        # Converteer de DataFrame naar een lijst van dicts (records)
        buildings_data = df.to_dict('records')
        total_records = len(buildings_data)

        # Houdt tellingen bij
        processed = 0
        successful = 0
        failed = 0

        # Bepaald batchgrootte
        batch_size = 100

        # Loop door de data in stappen van batch_size
        for i in range(0, total_records, batch_size):
            # Controleer of de gebruiker heeft gevraagd om te stoppen
            if st.session_state.stop_upload:
                status_text.text("⚠️ Upload gestopt door gebruiker")
                return False

            # Maak huidige batch
            batch = buildings_data[i:i + min(batch_size, total_records - i)]

            # Update status voor huidige batch
            status_text.text(f"🔄 Verwerken van records {i + 1} tot {i + len(batch)} van {total_records}")

            # Probeer deze batch te verwerken met de service
            try:
                # 'process_batch' is een fictieve methode in PODakenService,
                # deze moet daar gedefinieerd zijn om batches te kunnen verwerken.
                batch_success = po_daken_service.process_batch(batch)

                if batch_success:
                    successful += len(batch)
                else:
                    failed += len(batch)
            except Exception as e:
                # Fout bij het verwerken van deze batch
                logger.error(f"Batch fout: {str(e)}")
                failed += len(batch)

            # Update tellingen en voortgang
            processed = i + len(batch)
            progress = int((processed / total_records) * 100)
            progress_bar.progress(progress)

            # Toon (bij)gewerkte statistieken
            metrics_container.markdown(f"""
                ### Status
                - Verwerkt: {processed}/{total_records}
                - Succesvol: {successful}
                - Mislukt: {failed}
            """)

        # Als alle batches verwerkt zijn, geef True terug als er succesvol iets is verwerkt
        return successful > 0

    except Exception as e:
        # Als er een fout optreedt tijdens de gehele verwerking
        logger.error(f"Verwerkingsfout: {str(e)}")
        status_text.text(f"❌ Fout tijdens verwerking: {str(e)}")
        return False
