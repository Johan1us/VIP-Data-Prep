import streamlit as st

def create_header(environment: str = None) -> None:
    """
    Create the header section of the Streamlit app.

    Args:
        environment (str, optional): The selected environment (Acceptatie/Productie)
    """
    header_container = st.container()
    with header_container:
        col1, col2 = st.columns([6, 1])
        with col1:
            title = "VIP data voorbereiding"
            if environment:
                title += f" {environment.upper()}"
            st.title(title)
