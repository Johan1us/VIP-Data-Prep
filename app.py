import streamlit as st
import pandas as pd
import requests
import json

def validate_csv_structure(df):
    validation_errors = {
        'critical': [],
        'warnings': []
    }
    
    # Check if the dataframe is empty
    if df.empty:
        validation_errors['critical'].append("Het CSV-bestand is leeg")
        return validation_errors
        
    # Check mandatory columns
    required_columns = [
        'Objecttype',
        'Clustercode',
        'Dakpartner',
        'Betrokken Projectleider Techniek Daken',
        'Jaar laatste dakonderhoud',
        'Dakveiligheidsvoorzieningen aangebracht?',
        'Bliksembeveiliging',
        'Antenneopstelplaats'
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        validation_errors['critical'].append({
            'message': "Ontbrekende verplichte kolommen",
            'details': missing_columns
        })
    
    # Check for empty values in mandatory columns
    if not missing_columns:
        for col in required_columns:
            empty_count = df[col].isna().sum()
            if empty_count > 0:
                validation_errors['warnings'].append({
                    'message': f"Lege waarden gevonden in kolom '{col}'",
                    'details': f"{empty_count} rijen hebben geen waarde"
                })
    
    # Check for duplicate rows
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        validation_errors['warnings'].append({
            'message': "Dubbele rijen gedetecteerd",
            'details': f"{duplicate_count} dubbele rijen gevonden"
        })
    
    return validation_errors

def main():
    st.title("VIP Data Voorbereiding")
    
    st.header("📤 Data Upload")
    st.write("Upload uw CSV-bestand om te beginnen met de datavoorbereiding.")
    
    uploaded_file = st.file_uploader(
        "Kies een CSV-bestand",
        type="csv",
        help="Upload een CSV-bestand om uw data te bekijken en voor te bereiden"
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV file with semicolon separator
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
            
            # Display basic information about the dataset
            st.header("📊 Data Overzicht")
            st.write(f"**Aantal rijen:** {df.shape[0]}")
            st.write(f"**Aantal kolommen:** {df.shape[1]}")
            
            # Show column names
            st.subheader("Kolommen in uw dataset:")
            st.write(", ".join(df.columns.tolist()))
            
            # Display the first few rows of the data
            st.subheader("Voorbeeld van uw data:")
            st.dataframe(df.head())
            
            # Validate CSV structure
            st.header("🔍 Validatie Resultaten")
            validation_errors = validate_csv_structure(df)
            
            if validation_errors['critical']:
                st.error("Kritieke problemen die opgelost moeten worden:")
                for error in validation_errors['critical']:
                    if isinstance(error, dict):
                        st.markdown(f"- **{error['message']}**")
                        st.markdown("  - " + "\n  - ".join(error['details']))
                    else:
                        st.markdown(f"- {error}")
                st.info("📝 Tip: Los deze kritieke problemen op in uw data en upload het bestand opnieuw.")
            else:
                if validation_errors['warnings']:
                    st.warning("Waarschuwingen die aandacht nodig hebben:")
                    for warning in validation_errors['warnings']:
                        st.markdown(f"- **{warning['message']}**")
                        st.markdown(f"  - {warning['details']}")
                    st.info("📝 Tip: U kunt doorgaan met uploaden, maar het wordt aangeraden deze waarschuwingen te controleren.")
                else:
                    st.success("✅ Uw CSV-bestand heeft alle validatiecontroles doorstaan!")

                # Convert DataFrame to JSON
                json_data = df.to_json(orient='records', force_ascii=False)
                
                # Display JSON preview
                st.subheader("🔄 JSON Preview")
                with st.expander("Bekijk JSON data"):
                    st.json(json_data)
                
                # Add upload button
                if st.button("📤 Upload naar API"):
                    try:
                        # TODO: Replace with actual API endpoint and implementation
                        # Example implementation:
                        # response = requests.post(
                        #     'your-api-endpoint',
                        #     json=json.loads(json_data),
                        #     headers={'Content-Type': 'application/json'}
                        # )
                        st.info("Simulating API upload...")
                        st.success("✅ Data succesvol geüpload naar API!")
                        
                        # Offer JSON download as fallback
                        st.download_button(
                            label="⬇️ Download JSON",
                            file_name="data.json",
                            mime="application/json",
                            data=json_data
                        )
                    except Exception as e:
                        st.error(f"API Upload fout: {str(e)}")

        except Exception as e:
            st.error(f"Fout: {str(e)}")
            st.write("Zorg ervoor dat u een geldig CSV-bestand heeft geüpload.")

if __name__ == "__main__":
    main()
