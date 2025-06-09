import streamlit as st
import pandas as pd

# Impostazioni pagina: DEVE essere la PRIMA istruzione Streamlit nel file
st.set_page_config(page_title="Gestione Spese", layout="wide")

# Funzione per caricare e cache il dataframe delle spese dal file Excel su Google Drive
@st.cache_data
def carica_spese():
    # Link diretto per scaricare il file Excel da Google Drive usando l'ID
    url = "https://docs.google.com/uc?export=download&id=1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
    # Leggi il foglio 'Spese 2025' dal file Excel
    df = pd.read_excel(url, sheet_name='Spese 2025')
    return df

# Carica i dati
df_spese = carica_spese()

# Mostra le prime righe per controllo
st.header("Spese - dati grezzi")
st.dataframe(df_spese)

# Qui metti il codice per la dashboard (semplice esempio)

# Supponiamo che il dataframe abbia colonne: 'Testo', 'Valore', 'Tag' (controlla tu!)
# Creiamo una colonna 'Categoria' in base al tag (puoi modificare mappatura)
def categoria_per_tag(tag):
    entrate = ["stipendio", "bonus", "interessi"]
    uscite_necessarie = ["affitto", "bollette", "spesa"]
    uscite_variabili = ["ristorante", "shopping", "tempo libero"]
    tag = str(tag).lower()
    if tag in entrate:
        return "Entrate"
    elif tag in uscite_necessarie:
        return "Uscite necessarie"
    elif tag in uscite_variabili:
        return "Uscite variabili"
    else:
        return "Altro"

df_spese['Categoria'] = df_spese['Tag'].apply(categoria_per_tag)

# Calcolo somma per categoria
sintesi = df_spese.groupby('Categoria')['Valore'].sum()

st.header("Sintesi spese per categoria")
st.table(sintesi)

# Puoi aggiungere qui la tua logica di dashboard più complessa

