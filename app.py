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

    # Estrai i nomi dei mesi dalla prima riga, escludendo la prima colonna ("Testo")
    raw_mesi = df_raw.iloc[0, 1:]
    num_colonne_mese = 2  # ogni mese ha 2 colonne: Valore e Tag
    num_blocchi = (raw_mesi.shape[0]) // num_colonne_mese
    mesi = raw_mesi[::2].tolist()  # Prendo solo i nomi dei mesi (colonne Valore)

    dati = df_raw.iloc[1:, :]  # escludo la riga intestazione mesi

    df_lista = []

    for i in range(num_blocchi):
        try:
            blocco = dati.iloc[:, [0, 1 + i * 2, 2 + i * 2]].copy()
            blocco.columns = ["Testo", "Valore", "Tag"]
            blocco["Mese"] = mesi[i]
            df_lista.append(blocco)
        except IndexError:
            # In caso di colonne mancanti (incomplete) ignoro il blocco
            continue

    df = pd.concat(df_lista, ignore_index=True)
    df.dropna(subset=["Valore", "Tag"], inplace=True)

    def categoria_per_tag(tag):
        tag_str = str(tag).lower()
        if tag_str in ["stipendio", "bonus"]:
            return "Entrate"
        elif tag_str in ["affitto", "bollette", "spesa"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)

    return df


# Calcolo della dashboard
def calcola_dashboard(df_spese):
    # Pivot table: somma dei valori per Categoria e Mese
    pivot = pd.pivot_table(
        df_spese,
        values="Valore",
        index="Categoria",
        columns="Mese",
        aggfunc="sum",
        fill_value=0
    )

    # Assicuro che le categorie fondamentali esistano (altrimenti le creo con zeri)
    for cat in ["Entrate", "Uscite necessarie", "Uscite variabili"]:
        if cat not in pivot.index:
            pivot.loc[cat] = 0

    # Calcolo le Uscite come somma di Uscite necessarie e variabili
    pivot.loc["Uscite"] = pivot.loc["Uscite necessarie"] + pivot.loc["Uscite variabili"]

    # Calcolo il Risparmio mese (Entrate - Uscite)
    pivot.loc["Risparmio mese"] = pivot.loc["Entrate"] - pivot.loc["Uscite"]

    # Calcolo il Risparmio cumulato come somma progressiva del Risparmio mese
    pivot.loc["Risparmio cumulato"] = pivot.loc["Risparmio mese"].cumsum()

    # Riordino le righe secondo l’ordine desiderato
    ordine = [
        "Entrate",
        "Uscite necessarie",
        "Uscite variabili",
        "Uscite",
        "Risparmio mese",
        "Risparmio cumulato"
    ]
    pivot = pivot.reindex(ordine)

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
