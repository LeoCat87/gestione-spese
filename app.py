import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"

# === CATEGORIZZAZIONE ===
def categoria_per_tag(tag):
    if tag in ["Stipendio", "Entrate extra"]:
        return "Entrate"
    elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
        return "Uscite necessarie"
    else:
        return "Uscite variabili"

# === FUNZIONI ===
@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=1)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Valore", "Tag"])
    df = df.reset_index(drop=True)
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)
    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    return df

@st.cache_data
def carica_riepilogo():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === DASHBOARD DINAMICA ===
def calcola_dashboard_dinamica(df_spese):
    mesi = [col for col in df_spese.columns if isinstance(col, str)]
    dati = {"Entrate": {}, "Uscite necessarie": {}, "Uscite variabili": {}, "Risparmio mese": {}, "Risparmio cumulato": {}}
    cumulato = 0
    for mese in mesi:
        df_mese = df_spese[["Descrizione", "Valore", "Tag", "Categoria", mese]].dropna(subset=[mese])
        df_mese["Valore_mese"] = df_mese[mese] * df_mese["Valore"]
        for cat in ["Entrate", "Uscite necessarie", "Uscite variabili"]:
            totale = df_mese[df_mese["Categoria"] == cat]["Valore_mese"].sum()
            dati[cat][mese] = totale
        risparmio = dati["Entrate"][mese] - dati["Uscite necessarie"][mese] - dati["Uscite variabili"][mese]
        cumulato += risparmio
        dati["Risparmio mese"][mese] = risparmio
        dati["Risparmio cumulato"][mese] = cumulato
    df_dashboard = pd.DataFrame(dati).T
    df_dashboard["Total"] = df_dashboard.sum(axis=1)
    return df_dashboard

# === UI ===
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
    df_riep = carica_riepilogo()
    df_format = df_riep.applymap(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)
    st.dataframe(df_format, use_container_width=True, hide_index=True)

# === VISTA 3 ===
elif vista == "Dashboard":
    st.title("📈 Dashboard")
    df_spese = carica_spese()
    df_dash = calcola_dashboard_dinamica(df_spese)

    # Formattazione
    df_formattato = df_dash.copy()
    for col in df_formattato.columns:
        df_formattato[col] = df_formattato[col].apply(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_formattato, use_container_width=True)

    # Grafico
    st.subheader("📉 Andamento mensile per categoria")
    df_valori = df_dash.drop(columns=["Total"])
    df_valori = df_valori.transpose()  # mesi come righe

    fig, ax = plt.subplots(figsize=(12, 6))
    df_valori.plot(kind="bar", ax=ax)
    ax.set_ylabel("Importo (€)")
    ax.set_xlabel("Mese")
    ax.set_title("Entrate, Uscite e Risparmi per mese")
    ax.legend(title="Categoria")
    plt.xticks(rotation=45)
    st.pyplot(fig)
