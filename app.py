import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown

st.set_page_config(page_title="Gestione Spese", layout="wide")

# === CONFIGURAZIONE ===
GDRIVE_FILE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
EXCEL_PATH = "Spese_Leo.xlsx"

# Scarica il file Excel da Google Drive
@st.cache_data
def scarica_excel_da_drive():
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    gdown.download(url, EXCEL_PATH, quiet=True)

scarica_excel_da_drive()

# === FUNZIONI DI CARICAMENTO ===

@st.cache_data
def carica_spese():
    # Leggi prima riga per i mesi
    mesi = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", nrows=1, header=None).iloc[0, 2:]  # salto primi 2 campi "Testo" e "Valore"
    mesi = mesi.fillna("").tolist()

    # Leggi dati da seconda riga in poi, con intestazioni corrette
    df_raw = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=1)
    df_raw = df_raw.loc[:, ~df_raw.columns.str.contains('^Unnamed')]

    # Colonne "Testo" e "Tag" sono fisse, poi le colonne dei mesi a partire dalla terza colonna
    # Trasformiamo il df da wide a long per avere una colonna "Mese" e "Valore"
    df_long = df_raw.melt(id_vars=["Testo", "Tag"], var_name="Mese", value_name="Valore")

    # Sostituiamo i nomi colonne mesi con i nomi reali dalla prima riga
    # Poiché il melt ha preso nomi colonne come stringhe (es. 'Gennaio', 'Febbraio', ecc)
    # ma per sicurezza, se c'è discrepanza, mappiamo:
    mappa_mesi = dict(zip(df_raw.columns[2:], mesi))
    df_long["Mese"] = df_long["Mese"].map(mappa_mesi).fillna(df_long["Mese"])

    # Pulizia dati
    df_long = df_long.dropna(subset=["Valore", "Tag"])
    df_long["Valore"] = pd.to_numeric(df_long["Valore"], errors="coerce").fillna(0)

    # Categoria da Tag
    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df_long["Categoria"] = df_long["Tag"].apply(categoria_per_tag)
    return df_long

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===

st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Dashboard dinamica"])

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

elif vista == "Dashboard dinamica":
    st.title("📈 Dashboard dinamica")

    df_spese = carica_spese()

    # Pivot: somma Valore per Categoria e Mese
    df_pivot = pd.pivot_table(
        df_spese,
        index="Categoria",
        columns="Mese",
        values="Valore",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Total"
    )

    # Calcola Risparmio mese = Entrate - (Uscite necessarie + Uscite variabili)
    if all(x in df_pivot.index for x in ["Entrate", "Uscite necessarie", "Uscite variabili"]):
        risparmio = df_pivot.loc["Entrate"] - (df_pivot.loc["Uscite necessarie"] + df_pivot.loc["Uscite variabili"])
        df_pivot.loc["Risparmio mese"] = risparmio
        df_pivot.loc["Risparmio cumulato"] = risparmio.cumsum()

    df_formattato = df_pivot.reset_index().rename(columns={"index": "Voce"})
    for col in df_formattato.columns[1:]:
        df_formattato[col] = df_formattato[col].apply(formatta_euro)

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_formattato, use_container_width=True, hide_index=True)

    # Grafico andamento
    categorie_grafico = ["Entrate", "Uscite necessarie", "Uscite variabili", "Risparmio mese", "Risparmio cumulato"]
    presenti = [cat for cat in categorie_grafico if cat in df_pivot.index]
    if presenti:
        df_grafico = df_pivot.loc[presenti].drop(columns=["Total"], errors="ignore").transpose()
        fig, ax = plt.subplots(figsize=(12, 6))
        df_grafico.plot(kind="bar", ax=ax)
        ax.set_ylabel("Importo (€)")
        ax.set_xlabel("Mese")
        ax.set_title("Entrate, Uscite e Risparmi per mese")
        ax.legend(title="Categoria")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("⚠️ Nessuna categoria utile trovata per il grafico.")

