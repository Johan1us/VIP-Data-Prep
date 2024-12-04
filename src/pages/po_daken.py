import streamlit as st
import logging
import pandas as pd
from services.po_daken_service import PODakenService

logger = logging.getLogger(__name__)

def render():
    """Render the PO Daken page"""
    st.title("PO Daken")

    try:
        # Initialize service
        po_daken_service = PODakenService()

        # Create tabs for download and upload
        tab1, tab2 = st.tabs(["Download Data", "Upload Updates"])

        # Download Tab
        with tab1:
            st.markdown("### 📥 Download PO Daken Dataset")
            if st.button("Download PO Daken Dataset"):
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    # Update status
                    status_text.text("🔄 Authenticating...")
                    progress_bar.progress(20)

                    # Get buildings
                    status_text.text("🏢 Fetching building data...")
                    progress_bar.progress(40)
                    buildings = po_daken_service.get_all_buildings()

                    if buildings:
                        # Update progress
                        status_text.text("📊 Processing data...")
                        progress_bar.progress(60)

                        # Export to Excel
                        status_text.text("📝 Generating Excel file...")
                        progress_bar.progress(80)
                        excel_data = po_daken_service.export_to_excel(buildings)

                        # Final status
                        progress_bar.progress(100)
                        if excel_data:
                            status_text.empty()  # Clear the status text
                            st.success("✅ PO Daken dataset succesvol gegenereerd!")

                            # Create a download button
                            st.download_button(
                                label="📥 Download Excel file",
                                data=excel_data,
                                file_name="PO_Daken_Dataset.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            status_text.empty()
                            st.error("❌ Er is een fout opgetreden bij het genereren van het bestand.")
                    else:
                        status_text.empty()
                        st.error("❌ Geen data beschikbaar om te exporteren.")

                    # Clean up
                    progress_bar.empty()

                except Exception as e:
                    error_msg = f"❌ Er is een fout opgetreden: {str(e)}"
                    logger.error(error_msg)
                    st.error(error_msg)
                    # Clean up
                    progress_bar.empty()
                    status_text.empty()

        # Upload Tab
        with tab2:
            st.markdown("### 📤 Upload Updated PO Daken Dataset")
            uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx'])

            if uploaded_file is not None:
                try:
                    # Show preview of the data
                    df = pd.read_excel(uploaded_file)
                    st.write("Preview of uploaded data:")
                    st.dataframe(df.head())

                    # Add validation button
                    if st.button("Validate and Upload Data"):
                        with st.spinner("Validating and uploading data..."):
                            try:
                                # Process and upload the data
                                success = po_daken_service.process_uploaded_data(df)
                                if success:
                                    st.success("✅ Data successfully uploaded!")
                                else:
                                    st.error("❌ Error uploading data")
                            except Exception as e:
                                st.error(f"❌ Error processing data: {str(e)}")
                                logger.error(f"Error processing uploaded data: {str(e)}")

                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
                    logger.error(f"Error reading uploaded file: {str(e)}")

    except Exception as e:
        error_msg = f"❌ Er is een fout opgetreden bij het initialiseren van de service: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
