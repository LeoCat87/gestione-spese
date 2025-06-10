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
    # Leggi la prima riga (header dei mesi e tipi di colonne)
    header_1 = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", nrows=1, header=None).iloc[0]

    # Leggi tutto il dataframe saltando la prima riga
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=1)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    dati = []
    n_colonne = len(df.columns)

    # Ogni mese ha 3 colonne: Testo, Valore, Tag
    # Scorriamo a step 3
    for i in range(0, n_colonne, 3):
        mese = header_1[i]  # nome del mese nella prima riga
        # Prendi le 3 colonne del mese corrente
        df_mese = df.iloc[:, i:i+3]
        df_mese.columns = ["Testo", "Valore", "Tag"]

        df_mese["Mese"] = mese
        dati.append(df_mese)

    # Unisci tutti i dati per mese
    df_lungo = pd.concat(dati, ignore_index=True)

    # Pulisci valori e filtra
    df_lungo = df_lungo.dropna(subset=["Valore", "Tag"])
    df_lungo["Valore"] = pd.to_numeric(df_lungo["Valore"], errors="coerce").fillna(0)

    # Definisci categoria in base al tag
    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df_lungo["Categoria"] = df_lungo["Tag"].apply(categoria_per_tag)

    return df_lungo


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

