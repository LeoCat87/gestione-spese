import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"

# === FUNZIONI DI CARICAMENTO ===

@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Valore", "Tag"])
    df = df.reset_index(drop=True)
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)

    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    return df

@st.cache_data
def carica_riepilogo():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===

st.set_page_config(page_title="Gestione Spese", layout="wide")
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

# === VISTA 1: SPESE DETTAGLIATE ===

if vista == "Spese dettagliate":
    st.title("📌 Spese Dettagliate")
    df_spese = carica_spese()

    col1, col2 = st.columns(2)
    with col1:
        categoria_sel = st.selectbox("Filtra per categoria:", ["Tutte"] + sorted(df_spese["Categoria"].unique()))
    with col2:
        tag_sel = st.selectbox("Filtra per tag:", ["Tutti"] + sorted(df_spese["Tag"].unique()))

    df_filtrato = df_spese.copy()
    if categoria_sel != "Tutte":
        df_filtrato = df_filtrato[df_filtrato["Categoria"] == categoria_sel]
    if tag_sel != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["Tag"] == tag_sel]

    df_filtrato["Valore"] = df_filtrato["Valore"].map(formatta_euro)

    st.dataframe(df_filtrato.drop(columns=["Categoria"]), use_container_width=True)

# === VISTA 2: RIEPILOGO MENSILE ===

elif vista == "Riepilogo mensile":
    st.title("📊 Riepilogo Mensile per Tag")
    df_riepilogo = carica_riepilogo()
    df_formattato = df_riepilogo.applymap(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)
    st.dataframe(df_formattato, use_container_width=True, hide_index=True)

# === VISTA 3: DASHBOARD ===

elif vista == "Dashboard":
    st.title("📈 Dashboard")

    df_spese = carica_spese()
    df_spese["Mese"] = pd.to_datetime(df_spese["Data"]).dt.strftime("%B")

    # Riepilogo per Categoria e Mese
    pivot = pd.pivot_table(df_spese, values="Valore", index="Categoria", columns="Mese", aggfunc="sum", fill_value=0)

    # Ordina mesi correttamente
    mesi_ordine = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                   "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    pivot = pivot.reindex(columns=[m for m in mesi_ordine if m in pivot.columns])

    # Aggiunge righe Risparmio mese e Risparmio cumulato
    pivot.loc["Risparmio mese"] = pivot.loc["Entrate"] - pivot.loc["Uscite necessarie"] - pivot.loc["Uscite variabili"]
    pivot.loc["Risparmio cumulato"] = pivot.loc["Risparmio mese"].cumsum()
    pivot["Total"] = pivot.sum(axis=1)

    # Tabella formattata
    df_formattato = pivot.applymap(formatta_euro)
    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_formattato, use_container_width=True)

    # Grafico
    st.subheader("📊 Andamento mensile per categoria")
    categorie_plot = ["Entrate", "Uscite necessarie", "Uscite variabili", "Risparmio mese", "Risparmio cumulato"]
    df_valori = pivot.loc[categorie_plot].drop(columns=["Total"], errors="ignore").transpose()

    fig, ax = plt.subplots(figsize=(12, 6))
    df_valori.plot(kind="bar", ax=ax)
    ax.set_ylabel("Importo (€)")
    ax.set_xlabel("Mese")
    ax.set_title("Entrate, Uscite e Risparmi per mese")
    ax.legend(title="Categoria")
    plt.xticks(rotation=45)
    st.pyplot(fig)
