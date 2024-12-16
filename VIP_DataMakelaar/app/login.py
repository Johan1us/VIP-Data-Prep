# import streamlit as st

# def check_credentials(username, password):
#     # Vervang dit met echte authenticatie logica (bijv. API-call, database check)
#     if username == "admin" and password == "secret":
#         return True
#     return False

# def show_login_page():
#     st.title("Inloggen")
#     username = st.text_input("Gebruikersnaam")
#     password = st.text_input("Wachtwoord", type="password")
#     if st.button("Login"):
#         if check_credentials(username, password):
#             st.session_state["logged_in"] = True
#             st.experimental_rerun()  # herlaad de pagina zodat we naar home kunnen
#         else:
#             st.error("Ongeldige inloggegevens")

# def main():
#     # Controleer of we al ingelogd zijn
#     if "logged_in" not in st.session_state:
#         st.session_state["logged_in"] = False

#     if st.session_state["logged_in"]:
#         st.success("Je bent ingelogd! Ga naar de Home pagina.")
#         # Eventueel knoppen om direct naar home te gaan, of gebruik pages
#         st.write("[Ga naar Home](./home)")
#     else:
#         show_login_page()

# if __name__ == "__main__":
#     main()
