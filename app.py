import streamlit as st
import pandas as pd

# Deve essere la prima istruzione Streamlit nel file
st.set_page_config(page_title="Gestione Spese", layout="wide")

# ID del file Google Drive
GOOGLE_DRIVE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"

@st.cache_data(ttl=600)
def carica_spese():
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DRIVE_ID}/export?format=xlsx"
    xls = pd.ExcelFile(url)
    df = pd.read_excel(xls, sheet_name="Spese 2025")

    # Aggiungiamo la colonna Categoria in base al Tag
    def categoria_per_tag(tag):
        tag = str(tag).lower()
        if tag in ["stipendio", "entrate", "reddito"]:
            return "Entrate"
        elif tag in ["affitto", "bollette", "spese fisse"]:
            return "Uscite necessarie"
        elif tag in ["cibo", "tempo libero", "viaggi"]:
            return "Uscite variabili"
        else:
            return "Altro"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    return df

# --- MAIN ---

st.title("Gestione Spese")

df_spese = carica_spese()

st.subheader("Spese dettagliate")
st.dataframe(df_spese)

