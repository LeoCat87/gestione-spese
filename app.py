import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestione Spese", layout="wide")

# Funzione per caricare il file Excel da Google Drive
@st.cache_data
def carica_file_excel():
    url = "https://docs.google.com/uc?export=download&id=1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
    xls = pd.ExcelFile(url)
    return xls

# Funzione per caricare il foglio "Spese 2025" come DataFrame
@st.cache_data
def carica_spese():
    xls = carica_file_excel()
    df = pd.read_excel(xls, sheet_name="Spese 2025")
    return df

# Mappatura Tag -> Categoria
def categoria_per_tag(tag):
    entrate = ["Stipendio", "Bonus"]
    uscite_necessarie = ["Affitto", "Bolletta", "Spesa"]
    uscite_variabili = ["Svago", "Ristorante"]

    if tag in entrate:
        return "Entrate"
    elif tag in uscite_necessarie:
        return "Uscite necessarie"
    elif tag in uscite_variabili:
        return "Uscite variabili"
    else:
        return "Altro"

df_spese = carica_spese()
df_spese["Categoria"] = df_spese["Tag"].apply(categoria_per_tag)

# Visualizzazione tabella spese
st.title("Spese dettagliate")
st.dataframe(df_spese)

# Visualizzazione dashboard statica (senza calcoli automatici)
st.title("Dashboard")
st.write("Qui andrà la dashboard, da implementare")

