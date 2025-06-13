import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
st.set_page_config(page_title="Gestione Spese", layout="wide")
# === CONFIGURAZIONE ===
GDRIVE_FILE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
EXCEL_PATH = "Spese_App.xlsx"
# Scarica il file Excel da Google Drive
@st.cache_data
def scarica_excel_da_drive():
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    gdown.download(url, EXCEL_PATH, quiet=True)
scarica_excel_da_drive()
# === FUNZIONI DI CARICAMENTO ===
@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese Leo", header=[1])
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
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo Leo", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df
@st.cache_data
def carica_dashboard():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo Leo", index_col=0)
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

    df_spese = carica_spese()

    # Estrai il nome dei mesi dalla riga di intestazione del file Excel
    mesi_excel = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                  "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

    # Trova il mese in base alla colonna in cui è stata trovata la riga
    # Nel tuo caso, ogni spesa è già stata associata a un mese nella struttura della tabella
    # Ma se manca la colonna "Mese", la creiamo in base alla colonna in cui si trovava la riga

    # Se non esiste già la colonna 'Mese', deducila dalla posizione del file
    if "Mese" not in df_spese.columns:
        df_spese["Mese"] = None
        sheet = pd.read_excel(EXCEL_PATH, sheet_name="Spese Leo", header=None)
        intestazioni = sheet.iloc[0].dropna().tolist()
        mesi_presenti = [m for m in intestazioni if m in mesi_excel]
        mese_corrente = None
        for col_idx in range(sheet.shape[1]):
            cell = sheet.iloc[0, col_idx]
            if cell in mesi_excel:
                mese_corrente = cell
            elif col_idx > 0 and sheet.iloc[1, col_idx] == "Valore":
                col_mese = mesi_presenti.pop(0)
                df_spese.loc[df_spese["Valore"].notna(), "Mese"] = col_mese

    # Riepilogo: somma per Tag e Mese
    df_riepilogo = df_spese.groupby(["Tag", "Mese"])["Valore"].sum().unstack(fill_value=0)

    # Riordina le colonne dei mesi
    df_riepilogo = df_riepilogo.reindex(columns=mesi_excel, fill_value=0)

    # Formatta in euro
    df_formattato = df_riepilogo.reset_index()
    df_formattato.columns = ["Categoria"] + mesi_excel
    for mese in mesi_excel:
        df_formattato[mese] = df_formattato[mese].apply(lambda x: formatta_euro(x) if x else "€ 0,00")

    st.dataframe(df_formattato, use_container_width=True)

# === VISTA 3: DASHBOARD ===
elif vista == "Dashboard":
    st.title("📈 Dashboard")

    df_riepilogo = carica_riepilogo()

    # === Mappa tag a macrocategorie ===
    mappa_macrocategorie = {
        "Entrate": ["Stipendio", "Affitto Savoldo 4 + generico"],
        "Uscite necessarie": [
            "PAC Investimenti", "Donazioni (StC, Unicef, Greenpeace)", "Mutuo", "Luce&Gas",
            "Internet/Telefono", "Mezzi", "Spese condominiali", "Spese comuni",
            "Auto (benzina, noleggio, pedaggi, parcheggi)", "Spesa cibo", "Tari", "Unobravo"
        ],
        "Uscite variabili": [
            "Amazon", "Bolli governativi", "Farmacia/Visite", "Food Delivery", "Generiche", "Multa",
            "Uscite (Pranzi,Cena,Apericena,Pub,etc)", "Prelievi", "Regali", "Sharing (auto, motorino, bici)",
            "Shopping (vestiti, mobili,...)", "Stireria", "Viaggi (treno, aereo, hotel, attrazioni, concerti, cinema)"
        ]
    }

    mesi = df_riepilogo.columns
    df_macrocategorie = pd.DataFrame(columns=mesi)

    for macro, sottotag in mappa_macrocategorie.items():
        tag_presenti = [t for t in sottotag if t in df_riepilogo.index]
        if tag_presenti:
            somma = df_riepilogo.loc[tag_presenti].sum()
        else:
            somma = pd.Series([0] * len(mesi), index=mesi)
        df_macrocategorie.loc[macro] = somma

    df_macrocategorie.loc["Risparmio mese"] = (
        df_macrocategorie.loc["Entrate"]
        - df_macrocategorie.loc["Uscite necessarie"]
        - df_macrocategorie.loc["Uscite variabili"]
    )
    df_macrocategorie.loc["Risparmio cumulato"] = df_macrocategorie.loc["Risparmio mese"].cumsum()

    # === Calcola la media fino al mese scorso ===
    from datetime import datetime
    mese_corrente = datetime.today().month
    mesi_da_includere = mesi[:mese_corrente - 1]  # solo fino al mese precedente
    df_macrocategorie["Media YTD"] = df_macrocategorie[mesi_da_includere].mean(axis=1)

    # === Tabella formattata ===
    df_tabella = df_macrocategorie.copy().reset_index().rename(columns={"index": "Voce"})
    for col in df_tabella.columns[1:]:
        df_tabella[col] = df_tabella[col].apply(lambda x: formatta_euro(x) if pd.notnull(x) else "€ 0,00")

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_tabella, use_container_width=True, hide_index=True)

    # === Grafico ===
    df_grafico = df_macrocategorie[mesi].transpose()
    st.subheader("📈 Andamento mensile")
    fig, ax = plt.subplots(figsize=(12, 6))
    df_grafico.plot(kind='bar', ax=ax)
    ax.set_title("Entrate, Uscite e Risparmio per mese")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Importo (€)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
