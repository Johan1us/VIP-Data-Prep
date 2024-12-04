import streamlit as st
from components.header import create_header
from pages import home, po_daken
from utils.logging_config import setup_logging
import hashlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Print to console
        logging.FileHandler('app.log')  # Save to file
    ]
)

logger = logging.getLogger(__name__)

setup_logging()

def check_password() -> bool:
    """Returns `True` if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    password = st.text_input("Wachtwoord", type="password")
    if password:
        if hashlib.sha256(password.encode()).hexdigest() == st.secrets["password"]:
            st.session_state.password_correct = True
            return True
        else:
            st.error("❌ Incorrect password")
            return False
    return False

def load_css():
    """Load custom CSS styles"""
    css_file_path = "../static/css/style.css"
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def initialize_session_state():
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

def main() -> None:
    """Main function to run the Streamlit application."""
    load_css()
    initialize_session_state()

    if not check_password():
        st.markdown(
            """
            <div style='padding: 2rem; max-width: 400px; margin: 0 auto;'>
                <h2 style='color: #2b579a; margin-bottom: 2rem;'>Login</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    create_header()

    # Navigation
    st.sidebar.title("Navigation")
    pages = {
        "Home": ("🏠", home.render),
        "PO Daken": ("🏢", po_daken.render)
    }

    selected_page = st.sidebar.radio(
        "Ga naar",
        list(pages.keys()),
        format_func=lambda x: f"{pages[x][0]} {x}"
    )

    st.session_state.current_page = selected_page

    # Render selected page
    pages[selected_page][1]()

    # Display settings and log sections
    if st.session_state.show_settings:
        with st.expander("⚙️ Instellingen", expanded=True):
            st.write("Configuratie opties hier...")

    with st.expander("📋 Log", expanded=False):
        for msg in st.session_state.log_messages:
            st.write(msg)

if __name__ == "__main__":
    main()
