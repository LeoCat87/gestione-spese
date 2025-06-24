import streamlit as st
import pandas as pd
import os
from datetime import datetime

# === Configurazione pagina ===
st.set_page_config(page_title="Gestione Spese", layout="wide")

# === Percorso file Excel ===
EXCEL_PATH = "Spese_App.xlsx"

# === Caricamento file iniziale se non esiste ===
if not os.path.exists(EXCEL_PATH):
    st.title("🔄 Carica file iniziale")
    uploaded_file = st.file_uploader("Carica il file 'Spese_App.xlsx'", type="xlsx")
    if uploaded_file:
        with open(EXCEL_PATH, "wb") as f:
            f.write(uploaded_file.read())
        st.success("✅ File caricato con successo.")
        st.info("🔁 Ora aggiorna la pagina per iniziare a usare l'app.")
    st.stop()

# === Sidebar: filtri globali ===
anno = st.sidebar.selectbox("📆 Anno", ["2024", "2025"], index=1)
persona = st.sidebar.selectbox("👤 Persona", ["Leo", "Ale", "Leo&Ale"], index=0)

# === Funzione nome foglio ===
def nome_foglio(prefix):
    return f"{prefix} {persona}" if anno == "2025" else f"{prefix} {persona} {anno}"

# === Caching dati ===
@st.cache_data
def carica_spese():
    sheet = pd.read_excel(EXCEL_PATH, sheet_name=nome_foglio("Spese"), header=None)
    mesi_excel = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                  "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    col_mese = {sheet.iloc[0, c].lower(): c for c in range(sheet.shape[1])
                if isinstance(sheet.iloc[0, c], str) and sheet.iloc[0, c].lower() in mesi_excel}
    spese = []
    for m, col in col_mese.items():
        intest = sheet.iloc[1, col:col+3].tolist()
        if "Valore" in intest and "Tag" in intest:
            blocco = sheet.iloc[2:, col:col+3].copy()
            blocco.columns = intest
            blocco["Mese"] = m.capitalize()
            spese.append(blocco)
    df = pd.concat(spese, ignore_index=True) if spese else pd.DataFrame()
    if not df.empty:
        df = df.dropna(subset=["Valore", "Tag"])
        df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)
        df["Testo"] = df.get("Testo", "").fillna("")
        df["Categoria"] = df["Tag"].apply(lambda tag: (
            "Entrate" if tag in ["Stipendio", "Entrate extra", "Affitto Savoldo 4 + generico"]
            else "Uscite necessarie" if tag in [
                "Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione",
                "PAC Investimenti", "Mutuo", "Luce&Gas", "Internet/Telefono", "Mezzi",
                "Spese condominiali", "Spese comuni", "Auto (benzina, noleggio, pedaggi, parcheggi)",
                "Spesa cibo", "Tari", "Unobravo", "Donazioni (StC, Unicef, Greenpeace)"
            ]
            else "Uscite variabili"
        ))
    return df

@st.cache_data
def carica_riepilogo():
    df = pd.read_excel(EXCEL_PATH, sheet_name=nome_foglio("Riepilogo"), index_col=0)
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === Navigazione ===
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

# === Caricamento viste ===
if vista == "Spese dettagliate":
    from viste.spese_dettagliate import mostra_spese_dettagliate
    mostra_spese_dettagliate(EXCEL_PATH, anno, persona, nome_foglio, carica_spese, carica_riepilogo, formatta_euro)

elif vista == "Riepilogo mensile":
    from viste.riepilogo_mensile import mostra_riepilogo_mensile
    mostra_riepilogo_mensile(EXCEL_PATH, nome_foglio, formatta_euro)

elif vista == "Dashboard":
    from viste.dashboard import mostra_dashboard
    mostra_dashboard(carica_riepilogo, formatta_euro, datetime)
