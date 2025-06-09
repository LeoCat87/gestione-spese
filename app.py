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

@st.cache_data
def carica_dashboard():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Dashboard 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df["Total"] = df["Total"].fillna(0)
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

    # Usa il nome dei mesi come colonna
    mesi = [col for col in pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=0).columns if col not in df_spese.columns]
    if not mesi:
        mesi = df_spese["Mese"].unique() if "Mese" in df_spese else []

    # Ricrea una colonna "Mese" basata sul layout del file
    df_raw = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
    df_raw = df_raw.loc[:, ~df_raw.columns.str.contains('^Unnamed')]
    mesi_riga = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=None).iloc[0]
    mesi_validi = mesi_riga.dropna().values

    df_raw["Mese"] = mesi_riga[df_raw.columns.get_loc("Descrizione")]  # o colonna con valori

    df = df_raw.copy()
    df = df.dropna(subset=["Valore", "Tag"])
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)

    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    df["Mese"] = mesi_riga[1]  # assegna il mese dalla prima riga

    # Calcola aggregati
    pivot = df.pivot_table(values="Valore", index="Categoria", columns="Mese", aggfunc="sum").fillna(0)

    # Aggiunge righe per risparmi
    if "Entrate" not in pivot.index:
        pivot.loc["Entrate"] = 0
    uscite_tot = pivot.get("Uscite necessarie", 0) + pivot.get("Uscite variabili", 0)
    risparmio_mensile = pivot.loc["Entrate"] - uscite_tot
    pivot.loc["Risparmio mese"] = risparmio_mensile
    pivot.loc["Risparmio cumulato"] = risparmio_mensile.cumsum()

    pivot["Total"] = pivot.sum(axis=1)
    df_dash = pivot.reset_index().rename(columns={"index": "Voce"})

    # Formatta
    for col in df_dash.columns[1:]:
        df_dash[col] = df_dash[col].apply(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_dash, use_container_width=True, hide_index=True)

    # Grafico
    st.subheader("📊 Andamento mensile per categoria")
    df_valori = pivot.loc[["Entrate", "Uscite necessarie", "Uscite variabili", "Risparmio mese", "Risparmio cumulato"]].transpose()
    fig, ax = plt.subplots(figsize=(12, 6))
    df_valori.plot(kind="bar", ax=ax)
    ax.set_ylabel("Importo (€)")
    ax.set_xlabel("Mese")
    ax.set_title("Entrate, Uscite e Risparmi per mese")
    ax.legend(title="Categoria")
    plt.xticks(rotation=45)
    st.pyplot(fig)
