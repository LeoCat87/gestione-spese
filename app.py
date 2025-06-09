import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"

# === FUNZIONI ===

@st.cache_data
def carica_spese():
    # Legge il foglio Spese 2025, usando la seconda riga come header
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=1)
    mese_riferimento = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=None).iloc[0, 0]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Valore", "Tag"])
    df = df.reset_index(drop=True)
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)

    # Categoria in base al Tag
    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    df["Mese"] = mese_riferimento  # assegna lo stesso mese a tutte le righe
    return df

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === APP ===

st.set_page_config(page_title="Gestione Spese", layout="wide")
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Dashboard"])

if vista == "Dashboard":
    st.title("Dashboard")
    df_spese = carica_spese()

    # Calcolo Dashboard dinamico
    df_pivot = df_spese.groupby(["Mese", "Categoria"])["Valore"].sum().unstack(fill_value=0)
    df_pivot["Risparmio mese"] = df_pivot.get("Entrate", 0) - df_pivot.get("Uscite necessarie", 0) - df_pivot.get("Uscite variabili", 0)
    df_pivot["Risparmio cumulato"] = df_pivot["Risparmio mese"].cumsum()
    df_pivot["Total"] = df_pivot.sum(axis=1)
    df_dash = df_pivot.transpose()

    # Ordina categorie
    ordina = ["Entrate", "Uscite necessarie", "Uscite variabili", "Risparmio mese", "Risparmio cumulato", "Total"]
    df_dash = df_dash.reindex([cat for cat in ordina if cat in df_dash.index])

    # Formattazione euro
    df_format = df_dash.applymap(formatta_euro)
    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_format.drop(columns=["Total"], errors="ignore"), use_container_width=True)

    # Grafico
    st.subheader("📊 Andamento mensile per categoria")
    df_valori = df_dash.drop(index="Total", errors="ignore")
    df_valori = df_valori.transpose()

    fig, ax = plt.subplots(figsize=(12, 6))
    df_valori.plot(kind="bar", ax=ax)
    ax.set_ylabel("Importo (€)")
    ax.set_title("Entrate, Uscite e Risparmi per mese")
    ax.legend(title="Categoria")
    plt.xticks(rotation=45)
    st.pyplot(fig)
