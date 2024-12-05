import streamlit as st
from services.api import get_api_client

def render():
    """Render the home page"""
    st.title("Home")
    api_client = get_api_client()

    if api_client.authenticate():
        # Add your existing home page functionality here
        st.write("Welcome to the main page!")
