import streamlit as st
import pandas as pd

def validate_csv_structure(df):
    validation_errors = []
    
    # Check if the dataframe is empty
    if df.empty:
        validation_errors.append("Het CSV-bestand is leeg")
        
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
        validation_errors.append(f"Ontbrekende verplichte kolommen: {', '.join(missing_columns)}")
    
    # Check for empty values in mandatory columns
    if not missing_columns:  # Only check if all required columns exist
        for col in required_columns:
            if df[col].isna().any():
                validation_errors.append(f"Kolom '{col}' bevat lege waarden.")
    
    # Check for duplicate rows
    if df.duplicated().any():
        validation_errors.append(f"Er zijn {df.duplicated().sum()} dubbele rijen gevonden")
    
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
            
            if validation_errors:
                st.warning("Let op: de volgende aandachtspunten zijn gevonden in uw CSV-bestand:")
                for error in validation_errors:
                    st.info(error)
            else:
                st.success("✅ Uw CSV-bestand heeft alle validatiecontroles doorstaan!")
                
        except Exception as e:
            st.error(f"Fout: {str(e)}")
            st.write("Zorg ervoor dat u een geldig CSV-bestand heeft geüpload.")

if __name__ == "__main__":
    main()
