import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

st.set_page_config(page_title="Gestione Spese", layout="wide")

# Funzione per scaricare il file da Google Drive
@st.cache_data
def scarica_file_excel_da_drive(file_id):
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    SERVICE_ACCOUNT_FILE = 'credentials.json'

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh

# ID del file su Google Drive
FILE_ID = '1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn'

# Carica il file Excel
@st.cache_data
def carica_file_excel():
    file_excel = scarica_file_excel_da_drive(FILE_ID)
    xls = pd.ExcelFile(file_excel)
    return xls

# Estrai i dati dal foglio "Spese 2025" in formato lungo
@st.cache_data
def carica_spese():
    xls = carica_file_excel()
    dati = pd.read_excel(xls, sheet_name='Spese 2025', header=None)

    mesi = dati.iloc[0, 1::3].tolist()
    df_lista = []

    for i, mese in enumerate(mesi):
        col_valore = 1 + i * 3
        col_tag = col_valore + 1

        blocco = dati.iloc[1:, [0, col_valore, col_tag]].copy()
        blocco.columns = ['Testo', 'Valore', 'Tag']
        blocco['Mese'] = mese
        df_lista.append(blocco)

    df_spese = pd.concat(df_lista, ignore_index=True)
    df_spese = df_spese.dropna(subset=['Valore'])
    df_spese['Valore'] = pd.to_numeric(df_spese['Valore'], errors='coerce')
    df_spese = df_spese.dropna(subset=['Valore'])
    return df_spese

# Mappa i tag in categorie macro per la dashboard
def categoria_per_tag(tag):
    if pd.isna(tag):
        return None
    tag = str(tag).lower()
    if tag == 'entrata':
        return 'Entrate'
    elif tag in ['affitto', 'bollette', 'spese mediche', 'trasporti', 'abbonamenti']:
        return 'Uscite necessarie'
    elif tag in ['spesa', 'svago', 'ristoranti', 'shopping', 'viaggi']:
        return 'Uscite variabili'
    else:
        return 'Altro'

# Calcola la dashboard dinamicamente dal foglio Spese 2025
def calcola_dashboard(df):
    df['Categoria'] = df['Tag'].apply(categoria_per_tag)

    pivot = pd.pivot_table(df, values='Valore', index='Categoria', columns='Mese', aggfunc='sum', fill_value=0)

    # Aggiungi Entrate, Uscite totali e Risparmi
    if 'Entrate' not in pivot.index:
        pivot.loc['Entrate'] = 0
    uscite_necessarie = pivot.loc['Uscite necessarie'] if 'Uscite necessarie' in pivot.index else 0
    uscite_variabili = pivot.loc['Uscite variabili'] if 'Uscite variabili' in pivot.index else 0
    pivot.loc['Uscite'] = uscite_necessarie + uscite_variabili
    pivot.loc['Risparmio mese'] = pivot.loc['Entrate'] - pivot.loc['Uscite']
    pivot.loc['Risparmio cumulato'] = pivot.loc['Risparmio mese'].cumsum(axis=1)

    # Aggiungi colonna Totale
    pivot['Totale'] = pivot.sum(axis=1)

    return pivot.loc[['Entrate', 'Uscite necessarie', 'Uscite variabili', 'Risparmio mese', 'Risparmio cumulato']]

# === APP ===
df_spese = carica_spese()
st.sidebar.title("Menu")
opzione = st.sidebar.radio("Seleziona vista", ["Spese dettagliate", "Dashboard"])

if opzione == "Spese dettagliate":
    st.title("Spese Dettagliate")
    st.dataframe(df_spese[['Testo', 'Valore', 'Tag']])

elif opzione == "Dashboard":
    st.title("Dashboard")
    df_dash = calcola_dashboard(df_spese)

    # Tabella
    st.dataframe(df_dash.style.format("{:,.0f} €"), use_container_width=True, hide_index=False)

    # Grafico
    fig, ax = plt.subplots(figsize=(12, 5))
    mesi = df_dash.columns[:-1]  # esclude 'Totale'
    ax.plot(mesi, df_dash.loc['Entrate', mesi], label='Entrate', marker='o')
    ax.plot(mesi, df_dash.loc['Uscite', mesi], label='Uscite', marker='o')
    ax.plot(mesi, df_dash.loc['Risparmio mese', mesi], label='Risparmio', marker='o')
    ax.plot(mesi, df_dash.loc['Risparmio cumulato', mesi], label='Risparmio cumulato', marker='o')

    ax.set_title('Andamento Mensile')
    ax.set_ylabel('€')
    ax.set_xlabel('Mese')
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)
