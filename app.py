import streamlit as st
import pandas as pd

# 📁 Nome del file Excel (deve essere caricato nella repo!)
EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"

st.set_page_config(page_title="Gestione Spese", layout="wide")

st.title("📊 Gestione Spese Personali")

@st.cache_data
def carica_spese():
    # Carica il foglio 'Spese' dal file Excel
    return pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE)

try:
    df = carica_spese()
    st.success("File caricato correttamente!")
    st.dataframe(df, use_container_width=True)
except FileNotFoundError:
    st.error(f"⚠️ Il file {EXCEL_PATH} non è stato trovato nella repository.")
except Exception as e:
    st.error(f"❌ Errore durante il caricamento: {e}")
