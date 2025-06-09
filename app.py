import streamlit as st
import pandas as pd
import io
import requests

# Deve essere il primo comando!
st.set_page_config(page_title="Gestione Spese", layout="wide")

# Carica il file Excel da Google Drive
@st.cache_data
def carica_file_drive():
    file_id = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
    url = f"https://drive.google.com/uc?id={file_id}"
    res = requests.get(url)
    if res.status_code != 200:
        st.error("Errore nel caricamento del file da Google Drive.")
        return None
    return io.BytesIO(res.content)

# Carica e trasforma i dati dal foglio 'Spese 2025'
@st.cache_data
def carica_spese():
    file = carica_file_drive()
    df_raw = pd.read_excel(file, sheet_name="Spese 2025", header=None)

    mesi = df_raw.iloc[0, 1:].tolist()
    dati = df_raw.iloc[1:, :]

    df_lista = []

    for i, mese in enumerate(mesi):
        blocco = dati.iloc[:, [0, i + 1, i + 2]].copy()
        blocco.columns = ["Testo", "Valore", "Tag"]
        blocco["Mese"] = mese
        df_lista.append(blocco)

    df = pd.concat(df_lista, ignore_index=True)
    df.dropna(subset=["Valore", "Tag"], inplace=True)

    def categoria_per_tag(tag):
        if str(tag).lower() in ["stipendio", "bonus"]:
            return "Entrate"
        elif str(tag).lower() in ["affitto", "bollette", "spesa"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    return df

# Calcolo della dashboard
def calcola_dashboard(df_spese):
    pivot = pd.pivot_table(df_spese, values="Valore", index="Categoria", columns="Mese", aggfunc="sum", fill_value=0)

    pivot.loc["Uscite"] = pivot.loc.get("Uscite necessarie", 0) + pivot.loc.get("Uscite variabili", 0)
    pivot.loc["Risparmio mese"] = pivot.loc.get("Entrate", 0) - pivot.loc["Uscite"]
    pivot.loc["Risparmio cumulato"] = pivot.loc["Risparmio mese"].cumsum(axis=1)
    pivot["Total"] = pivot.sum(axis=1)
    return pivot

# Avvio app
df_spese = carica_spese()

st.sidebar.title("Navigazione")
vista = st.sidebar.radio("Seleziona vista", ["Spese dettagliate", "Dashboard"])

if vista == "Spese dettagliate":
    st.title("Spese dettagliate")
    st.dataframe(df_spese[["Testo", "Valore", "Tag", "Categoria", "Mese"]])

elif vista == "Dashboard":
    st.title("Dashboard")

    df_dash = calcola_dashboard(df_spese)

    # Visualizzazione tabella senza indice numerico
    st.dataframe(df_dash.style.format("{:,.2f}"), use_container_width=True)

    # Grafico
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 6))
    mesi = df_dash.columns[:-1]  # esclude colonna 'Total'

    ax.plot(mesi, df_dash.loc["Entrate", mesi], label="Entrate", marker="o")
    ax.plot(mesi, df_dash.loc["Uscite", mesi], label="Uscite", marker="o")
    ax.plot(mesi, df_dash.loc["Risparmio mese", mesi], label="Risparmio mese", marker="o")
    ax.plot(mesi, df_dash.loc["Risparmio cumulato", mesi], label="Risparmio cumulato", marker="o")

    ax.set_title("Andamento Mensile")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Euro")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)
