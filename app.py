import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gestione Spese", layout="wide")

@st.cache_data
def carica_spese():
    # URL di download diretto dal file su Google Drive (ID specifico)
    url = "https://docs.google.com/uc?export=download&id=1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
    df = pd.read_excel(url, sheet_name='Spese 2025')
    return df

def categoria_per_tag(tag):
    entrate = ["stipendio", "bonus", "interessi"]
    uscite_necessarie = ["affitto", "bollette", "spesa"]
    uscite_variabili = ["ristorante", "shopping", "tempo libero"]

    tag_lower = str(tag).lower()
    if tag_lower in entrate:
        return "Entrate"
    elif tag_lower in uscite_necessarie:
        return "Uscite necessarie"
    elif tag_lower in uscite_variabili:
        return "Uscite variabili"
    else:
        return "Altro"

df_spese = carica_spese()
df_spese["Categoria"] = df_spese["Tag"].apply(categoria_per_tag)

st.title("Gestione Spese")

view = st.sidebar.selectbox("Scegli vista", ["Spese dettagliate", "Dashboard"])

if view == "Spese dettagliate":
    st.header("Spese Dettagliate")
    st.dataframe(df_spese[["Testo", "Valore", "Tag", "Categoria"]])

elif view == "Dashboard":
    st.header("Dashboard")
    # Qui la dashboard non calcola ancora aggregati, ma mostra i dati base
    pivot = pd.pivot_table(df_spese, values="Valore", index="Categoria", aggfunc="sum", fill_value=0)
    pivot = pivot.reindex(["Entrate", "Uscite necessarie", "Uscite variabili", "Altro"], fill_value=0)

    st.dataframe(pivot)

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    pivot.plot(kind="bar", ax=ax, legend=False)
    ax.set_ylabel("Euro")
    ax.set_title("Somme per Categoria")
    st.pyplot(fig)
