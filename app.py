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
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df["Total"] = df.get("Total", pd.Series(0))  # Se manca "Total", metti 0
    return df
 
def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
 
# === INTERFACCIA ===
 
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

    df_riepilogo = carica_riepilogo()

    # Definizione delle categorie
    categorie = {
        "Entrate": ["Stipendio", "Affitto Savoldo 4", "generico"],
        "Uscite necessarie": [
            "PAC Investimenti", "Donazioni (StC, Unicef, Greenpeace)", "Mutuo", "Luce&Gas",
            "Internet/Telefono", "Mezzi", "Spese condominiali", "Spese comuni", 
            "Auto (benzina, noleggio, pedaggi, parcheggi)", "Spesa cibo", "Tari", "Unobravo"
        ],
        "Uscite variabili": [
            "Amazon", "Bolli governativi", "Farmacia/Visite", "Food Delivery", "Generiche",
            "Multa", "Uscite (Pranzi,Cena,Apericena,Pub,etc)", "Prelievi", "Regali", 
            "Sharing (auto, motorino, bici)", "Shopping (vestiti, mobili,...)", "Stireria",
            "Viaggi (treno, aereo, hotel, attrazioni, concerti, cinema)"
        ],
    }

    # Calcolo macrocategorie
    df_dashboard = pd.DataFrame()
    for macro, sotto in categorie.items():
        presenti = [s for s in sotto if s in df_riepilogo.index]
        df_dashboard.loc[macro] = df_riepilogo.loc[presenti].sum()

    # Risparmio mese = Entrate - (Uscite necessarie + Uscite variabili)
    df_dashboard.loc["Risparmio mese"] = (
        df_dashboard.loc["Entrate"] -
        df_dashboard.loc["Uscite necessarie"] -
        df_dashboard.loc["Uscite variabili"]
    )

    # Risparmio cumulato = somma progressiva del risparmio mese
    df_dashboard.loc["Risparmio cumulato"] = df_dashboard.loc["Risparmio mese"].cumsum()

    # Tabella formattata
    df_formattato = df_dashboard.copy().reset_index().rename(columns={"index": "Voce"})
    for col in df_formattato.columns[1:]:
        df_formattato[col] = df_formattato[col].apply(
            lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x
        )

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_formattato, use_container_width=True, hide_index=True)

    # Grafico (solo 5 macrocategorie)
    df_valori = df_dashboard.transpose()[[
        "Entrate", "Uscite necessarie", "Uscite variabili", "Risparmio mese", "Risparmio cumulato"
    ]]
    st.subheader("📊 Andamento mensile per categoria")
    fig, ax = plt.subplots(figsize=(12, 6))
    df_valori.plot(kind="bar", ax=ax)
    ax.set_ylabel("Importo (€)")
    ax.set_xlabel("Mese")
    ax.set_title("Entrate, Uscite e Risparmi per mese")
    ax.legend(title="Categoria")
    plt.xticks(rotation=45)
    st.pyplot(fig)

