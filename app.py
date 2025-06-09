import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestione Spese", layout="wide")

@st.cache_data
def carica_file_excel():
    url = "https://docs.google.com/uc?export=download&id=1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
    xls = pd.ExcelFile(url)
    return xls

@st.cache_data
def carica_spese():
    xls = carica_file_excel()
    df = pd.read_excel(xls, sheet_name="Spese 2025")
    return df

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

# Attenzione: verifica che nella colonna 'Tag' non ci siano NaN o errori
if "Tag" in df_spese.columns:
    df_spese["Categoria"] = df_spese["Tag"].fillna("").apply(categoria_per_tag)
else:
    st.error("La colonna 'Tag' non è presente nel foglio 'Spese 2025'!")

st.title("Spese dettagliate")
st.dataframe(df_spese)
