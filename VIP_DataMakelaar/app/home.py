# import streamlit as st

# def main():
#     # Controleer of de gebruiker ingelogd is
#     if "logged_in" not in st.session_state or st.session_state["logged_in"] == False:
#         st.warning("Je moet eerst inloggen.")
#         st.write("[Ga naar Login](./login)")
#         return

#     st.title("VIP DataMakelaar - Home")

#     # Voorbeeld: datasets selecteren
#     # In een echte scenario haal je deze lijst op via API-client
#     datasets = ["po_daken", "po_gevels", "complex_algemeen", "eenheid_funderingen", "eenheid_ketel"]
#     selected_dataset = st.selectbox("Selecteer een dataset", datasets)

#     if st.button("Download Excel"):
#         # Hier zou je logica toevoegen om de Excel te genereren met excel_utils
#         st.success(f"Excel voor {selected_dataset} wordt gegenereerd...")
#         # generate_excel_file(...) etc.
#         st.write("Hier zou je een downloadlink aanbieden")

#     if st.button("Upload Bewerkt Excel"):
#         # File_uploader om excel terug te uploaden
#         uploaded_file = st.file_uploader("Upload je bijgewerkte Excel", type=["xlsx"])
#         if uploaded_file is not None:
#             # Verwerk upload
#             st.success("Upload geslaagd, validatie in progress...")
#             # valideren via logica, API calls etc.

# if __name__ == "__main__":
#     main()
