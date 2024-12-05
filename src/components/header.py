import streamlit as st

def create_header() -> None:
    """Create the header section of the Streamlit app."""
    header_container = st.container()
    with header_container:
        col1, col2 = st.columns([6, 1])
        with col1:
            st.title("VIP data voorbereiding")
