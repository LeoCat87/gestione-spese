import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"

# === FUNZIONI DI CARICAMENTO ===

@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
    mese = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=None).iloc[0, 0]
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Valore", "Tag"])
    df = df.reset_index(drop=True)
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)
    df["Mese"] = mese

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
def calcola_dashboard(df_spese):
    mesi = df_spese["Mese"].unique()
    categorie = ["Entrate", "Uscite necessarie", "Uscite variabili"]
    dati = {cat: [] for cat in categorie}
    risparmio_mese = []
    risparmio_cumulato = []
    totale = []
    cumulato = 0

    for mese in mesi:
        df_mese = df_spese[df_spese["Mese"] == mese]
        entrate = df_mese[df_mese["Categoria"] == "Entrate"]["Valore"].sum()
        uscite_n = df_mese[df_mese["Categoria"] == "Uscite necessarie"]["Valore"].sum()
        uscite_v = df_mese[df_mese["Categoria"] == "Uscite variabili"]["Valore"].sum()
        risparmio = entrate - uscite_n - uscite_v
        cumulato += risparmio

        dati["Entrate"].append(entrate)
        dati["Uscite necessarie"].append(uscite_n)
        dati["Uscite variabili"].append(uscite_v)
        risparmio_mese.append(risparmio)
        risparmio_cumulato.append(cumulato)

    df_dashboard = pd.DataFrame({
        mese: [
            dati["Entrate"][i],
            dati["Uscite necessarie"][i],
            dati["Uscite variabili"][i],
            risparmio_mese[i],
            risparmio_cumulato[i]
        ] for i, mese in enumerate(mesi)
    }, index=["Entrate", "Uscite necessarie", "Uscite variabili", "Risparmio mese", "Risparmio cumulato"])

    df_dashboard["Total"] = df_dashboard.sum(axis=1)
    return df_dashboard

# === FORMATTAZIONE ===

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===

st.set_page_config(page_title="Gestione Spese", layout="wide")
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

# === VISTA 1 ===
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

# === VISTA 2 ===
elif vista == "Riepilogo mensile":
    st.title("📊 Riepilogo Mensile per Tag")
    df_riepilogo = carica_riepilogo()
    df_formattato = df_riepilogo.applymap(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)
    st.dataframe(df_formattato, use_container_width=True, hide_index=True)

# === VISTA 3 ===
elif vista == "Dashboard":
    st.title("📈 Dashboard")
    df_spese = carica_spese()
    df_dash = calcola_dashboard(df_spese)

    col_index = df_dash.columns.get_loc("Total") + 1
    df_dash = df_dash.iloc[:, :col_index]

    df_formattato = df_dash.copy()
    for col in df_formattato.columns:
        df_formattato[col] = df_formattato[col].apply(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_formattato, use_container_width=True)

    df_valori = df_dash.drop(columns=["Total"]).transpose()
    st.subheader("📊 Andamento mensile per categoria")
    fig, ax = plt.subplots(figsize=(12, 6))
    df_valori.plot(kind="bar", ax=ax)
    ax.set_ylabel("Importo (€)")
    ax.set_xlabel("Mese")
    ax.set_title("Entrate, Uscite e Risparmi per mese")
    ax.legend(title="Categoria")
    plt.xticks(rotation=45)
    st.pyplot(fig)
