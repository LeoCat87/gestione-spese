import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"

# === FUNZIONI DI CARICAMENTO ===

@st.cache_data
def carica_spese_con_mese():
    df_raw = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
    mesi_riga = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=None).iloc[0]
    mese_rif = mesi_riga[df_raw.columns.get_loc("Testo")]
    df_raw["Mese"] = mese_rif

    df_raw = df_raw.loc[:, ~df_raw.columns.str.contains('^Unnamed')]
    df_raw = df_raw.dropna(subset=["Valore", "Tag"])
    df_raw = df_raw.reset_index(drop=True)
    df_raw["Valore"] = pd.to_numeric(df_raw["Valore"], errors="coerce").fillna(0)

    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df_raw["Categoria"] = df_raw["Tag"].apply(categoria_per_tag)
    return df_raw

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===

st.set_page_config(page_title="Gestione Spese", layout="wide")
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Dashboard"])

# === VISTA 1: SPESE DETTAGLIATE ===

if vista == "Spese dettagliate":
    st.title("📌 Spese Dettagliate")
    df_spese = carica_spese_con_mese()

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

# === VISTA 2: DASHBOARD ===

elif vista == "Dashboard":
    st.title("📈 Dashboard")
    df_spese = carica_spese_con_mese()

    pivot = df_spese.pivot_table(index="Categoria", columns="Mese", values="Valore", aggfunc="sum", fill_value=0)
    pivot = pivot.reindex(["Entrate", "Uscite necessarie", "Uscite variabili"])  # ordine desiderato

    pivot.loc["Risparmio mese"] = pivot.loc["Entrate"] - pivot.loc["Uscite necessarie"] - pivot.loc["Uscite variabili"]
    pivot.loc["Risparmio cumulato"] = pivot.loc["Risparmio mese"].cumsum()
    pivot["Total"] = pivot.sum(axis=1)

    df_mostrato = pivot.reset_index().rename(columns={"Categoria": "Voce"})
    for col in df_mostrato.columns[1:]:
        df_mostrato[col] = df_mostrato[col].apply(formatta_euro)

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_mostrato, use_container_width=True, hide_index=True)

    st.subheader("📊 Andamento mensile per categoria")
    pivot_grafico = pivot.drop(columns=["Total"]).transpose()

    fig, ax = plt.subplots(figsize=(12, 6))
    pivot_grafico.plot(kind="bar", ax=ax)
    ax.set_ylabel("Importo (€)")
    ax.set_xlabel("Mese")
    ax.set_title("Entrate, Uscite e Risparmi per mese")
    ax.legend(title="Categoria")
    plt.xticks(rotation=45)
    st.pyplot(fig)
