import streamlit as st
import pandas as pd

def main():
    st.title("VIP Data Prep Application")
    
    # Add file upload section with clear instructions
    st.header("📤 Data Upload")
    st.write("Please upload your CSV file to begin data preparation.")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="Upload a CSV file to preview and prepare your data"
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV file with semicolon separator
            df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
            
            # Display basic information about the dataset
            st.header("📊 Data Preview")
            st.write(f"**Number of rows:** {df.shape[0]}")
            st.write(f"**Number of columns:** {df.shape[1]}")
            
            # Show column names
            st.subheader("Columns in your dataset:")
            st.write(", ".join(df.columns.tolist()))
            
            # Display the first few rows of the data
            st.subheader("Preview of your data:")
            st.dataframe(df.head())
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.write("Please make sure you've uploaded a valid CSV file.")

if __name__ == "__main__":
    main() 