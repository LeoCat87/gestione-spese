import streamlit as st
import pandas as pd

EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"
FOGLIO_RIEPILOGO = "Riepilogo 2025"
FOGLIO_DASHBOARD = "Dashboard 2025"

# Mapping dei tag
CATEGORIE = {
    "Entrate": ["Stipendio", "Bonus", "Rimborso"],
    "Uscite Necessarie": ["Affitto", "Mutuo", "Bollette", "Spesa", "Trasporti", "Assicurazione", "Medico"],
    "Uscite Variabili": ["Ristorante", "Viaggio", "Abbigliamento", "Regali", "Tempo libero", "Altro"]
}

def categoria_per_tag(tag):
    for cat, tag_list in CATEGORIE.items():
        if tag in tag_list:
            return cat
    return "Altro"

@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE, header=[0, 1])
    dati = []
    for mese in df.columns.levels[0]:
        if pd.isna(mese):
            continue
        try:
            blocco = df[mese][['Testo', 'Valore', 'Tag']].dropna(how='all')
            blocco = blocco.rename(columns={"Testo": "Testo", "Valore": "Importo", "Tag": "Tag"})
            blocco["Mese"] = mese
            dati.append(blocco)
        except KeyError:
            continue
    completo = pd.concat(dati, ignore_index=True)
    completo = completo.dropna(subset=["Importo"])
    completo["Categoria"] = completo["Tag"].apply(categoria_per_tag)
    return completo

@st.cache_data
def carica_riepilogo():
    return pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_RIEPILOGO)

@st.cache_data
def carica_dashboard():
    return pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_DASHBOARD)

# Sidebar per selezionare la vista
st.sidebar.title("Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["📊 Dashboard", "🧾 Riepilogo 2025", "📂 Spese dettagliate"])

# Vista: Dashboard
if vista == "📊 Dashboard":
    st.title("📊 Dashboard Mensile")
    df = carica_dashboard()
    st.dataframe(df)

# Vista: Riepilogo
elif vista == "🧾 Riepilogo 2025":
    st.title("🧾 Riepilogo per Tag e Mese")
    df = carica_riepilogo()
    st.dataframe(df)

# Vista: Spese dettagliate
elif vista == "📂 Spese dettagliate":
    st.title("📂 Spese dettagliate")
    df = carica_spese()
    
    st.dataframe(df)

    st.subheader("Totali per Categoria")
    tot_cat = df.groupby("Categoria")["Importo"].sum().reset_index()
    st.dataframe(tot_cat)

    st.subheader("Filtro per mese")
    mesi = sorted(df["Mese"].unique())
    mese_sel = st.selectbox("Seleziona un mese", mesi)
    st.dataframe(df[df["Mese"] == mese_sel])
