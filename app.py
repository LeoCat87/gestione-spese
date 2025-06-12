import streamlit as st
import pandas as pd
import gdown
import openpyxl
import matplotlib.pyplot as plt
import os
import io

st.set_page_config(page_title="Gestione Spese", layout="wide")

# === CONFIGURAZIONE ===
GDRIVE_FILE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
EXCEL_FILE = "Spese_App.xlsx"

# Scarica il file Excel da Google Drive
@st.cache_data
def scarica_excel_da_drive():
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    gdown.download(url, EXCEL_FILE, quiet=True)

scarica_excel_da_drive()

# === FUNZIONI DI CARICAMENTO ===
@st.cache_data
def carica_spese():
    df_raw = pd.read_excel(EXCEL_FILE, sheet_name="Spese Leo", header=1)
    df_raw = df_raw.loc[:, ~df_raw.columns.str.contains("^Unnamed")]

    mesi = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]

    records = []

    for i, mese in enumerate(mesi):
        col_base = i * 3
        if col_base + 2 < len(df_raw.columns):
            sotto_df = df_raw.iloc[:, col_base:col_base+3].copy()
            sotto_df.columns = ["Testo", "Valore", "Tag"]
            sotto_df = sotto_df.dropna(how="all", subset=["Valore", "Testo", "Tag"])
            sotto_df["Mese"] = mese.lower()
            sotto_df["Tag"] = sotto_df["Tag"].fillna('').astype(str).str.strip().str.capitalize()
            sotto_df["Testo"] = sotto_df["Testo"].fillna('').astype(str).str.strip()
            sotto_df["Valore"] = pd.to_numeric(sotto_df["Valore"], errors="coerce")
            records.append(sotto_df)

    df_finale = pd.concat(records, ignore_index=True)
    return df_finale

@st.cache_data
def carica_riepilogo_originale():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name="Riepilogo Leo", index_col=0)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        return df
    except Exception as e:
        st.error(f"Errore durante il caricamento del riepilogo: {e}")
        st.stop()

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===

st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

# === VISTA 1: SPESE DETTAGLIATE ===
# (rimane invariata)

# === VISTA 2: RIEPILOGO MENSILE ===
elif vista == "Riepilogo mensile":
    st.title("\U0001F4CA Riepilogo Mensile (dinamico)")

    df_spese = carica_spese()
    df_orig = carica_riepilogo_originale()

    macrocategorie = {
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

    mesi_ordinati = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
    ]

    df_spese["Mese"] = df_spese["Mese"].str.lower().str.strip()
    df_spese["Tag"] = df_spese["Tag"].str.strip()
    df_spese = df_spese[df_spese["Mese"].isin(mesi_ordinati)]

    df_riep_dyn = df_spese.groupby(["Tag", "Mese"])["Valore"].sum().unstack(fill_value=0)
    df_riep_dyn = df_riep_dyn[[m for m in mesi_ordinati if m in df_riep_dyn.columns]]

    df_base = df_orig.copy()
    df_base = df_base.loc[:, ~df_base.columns.duplicated()]

    for mese in mesi_ordinati:
        if mese in df_riep_dyn.columns:
            mese_nome = mese.capitalize()
            df_base[mese_nome] = df_riep_dyn[mese].reindex(df_base.index).fillna(0)

    righe_finali = []
    for categoria, tag_list in macrocategorie.items():
        intestazione = pd.Series([None] * len(mesi_ordinati), index=[m.capitalize() for m in mesi_ordinati], name=categoria)
        righe_finali.append(intestazione)
        for tag in tag_list:
            if tag in df_base.index:
                righe_finali.append(df_base.loc[tag])

    df_riep_cat = pd.DataFrame(righe_finali)

    df_formattato = df_riep_cat.copy()
    for col in df_formattato.columns:
        df_formattato[col] = df_formattato[col].apply(
            lambda x: formatta_euro(x) if pd.notnull(x) and isinstance(x, (int, float)) else ""
        )

    st.dataframe(df_formattato, use_container_width=True, hide_index=False)
