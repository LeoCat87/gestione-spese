
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from viste.spese_dettagliate import mostra_spese_dettagliate
from viste.riepilogo_mensile import mostra_riepilogo_mensile
from viste.dashboard import mostra_dashboard

st.set_page_config(page_title="Gestione Spese", layout="wide")

EXCEL_PATH = "Spese_App.xlsx"

if not os.path.exists(EXCEL_PATH):
    st.title("🔄 Carica file iniziale")
    uploaded_file = st.file_uploader("Carica il file 'Spese_App.xlsx'", type="xlsx")
    if uploaded_file:
        with open(EXCEL_PATH, "wb") as f:
            f.write(uploaded_file.read())
        st.success("✅ File caricato con successo.")
        st.info("🔁 Ora aggiorna manualmente la pagina per iniziare a usare l'app.")
    st.stop()

anno = st.sidebar.selectbox("📆 Anno", ["2024", "2025"], index=1)
persona = st.sidebar.selectbox("👤 Persona", ["Leo", "Ale", "Leo&Ale"], index=0)

def nome_foglio(prefix, anno, persona):
    if anno == "2025":
        return f"{prefix} {persona}"
    else:
        return f"{prefix} {persona} {anno}"

@st.cache_data(show_spinner=False)
def carica_spese(anno: str, persona: str):
    nome_sheet = nome_foglio("Spese", anno, persona)
    st.write(f"📄 Caricamento foglio: `{nome_sheet}`")  # Debug

    sheet = pd.read_excel(EXCEL_PATH, sheet_name=nome_sheet, header=None)

    mesi_excel = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                  "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

    col_mese = {}
    for col_idx in range(sheet.shape[1]):
        cella = str(sheet.iloc[0, col_idx]).strip().lower()
        if cella in mesi_excel:
            col_mese[cella] = col_idx

    st.write(f"🧩 Foglio caricato: {sheet.shape[0]} righe, {sheet.shape[1]} colonne")
    st.write("🔎 Colonne identificate come mesi:")
    st.write(col_mese)

    spese = []
    for mese_lower, start_col in col_mese.items():
        intestazioni = sheet.iloc[1, start_col:start_col+3].tolist()
        st.write(f"➡️ Analisi mese: {mese_lower.capitalize()} (colonna {start_col})")
        st.write(f"Intestazioni rilevate: {intestazioni}")

        if "Valore" in intestazioni and "Tag" in intestazioni:
            df_blocco = sheet.iloc[2:, start_col:start_col+3].copy()
            df_blocco.columns = intestazioni
            df_blocco["Mese"] = mese_lower.capitalize()
            spese.append(df_blocco)

    if spese:
        df = pd.concat(spese, ignore_index=True)
        df = df.dropna(subset=["Valore", "Tag"])
        df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)
        df["Testo"] = df.get("Testo", "").fillna("")

        def categoria_per_tag(tag):
            if tag in ["Stipendio", "Entrate extra", "Affitto Savoldo 4 + generico"]:
                return "Entrate"
            elif tag in [
                "Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione",
                "PAC Investimenti", "Mutuo", "Luce&Gas", "Internet/Telefono", "Mezzi",
                "Spese condominiali", "Spese comuni", "Auto (benzina, noleggio, pedaggi, parcheggi)",
                "Spesa cibo", "Tari", "Unobravo", "Donazioni (StC, Unicef, Greenpeace)"
            ]:
                return "Uscite necessarie"
            else:
                return "Uscite variabili"

        df["Categoria"] = df["Tag"].apply(categoria_per_tag)
        return df
    else:
        st.warning("⚠️ Nessuna spesa trovata nei blocchi mensili del foglio.")
        return pd.DataFrame(columns=["Testo", "Valore", "Tag", "Mese", "Categoria"])

@st.cache_data(show_spinner=False)
def carica_riepilogo(anno: str, persona: str):
    nome_sheet = nome_foglio("Riepilogo", anno, persona)
    st.write(f"📄 Caricamento foglio: `{nome_sheet}`")  # <-- DEBUG VISIBILE

    df = pd.read_excel(EXCEL_PATH, sheet_name=nome_sheet, index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

if vista == "Spese dettagliate":
    mostra_spese_dettagliate(EXCEL_PATH, anno, persona, lambda prefix: nome_foglio(prefix, anno, persona), carica_spese, carica_riepilogo, formatta_euro)

elif vista == "Riepilogo mensile":
    mostra_riepilogo_mensile(EXCEL_PATH, lambda prefix: nome_foglio(prefix, anno, persona), formatta_euro)

elif vista == "Dashboard":
    mostra_dashboard(lambda: carica_riepilogo(anno, persona), formatta_euro, datetime)
