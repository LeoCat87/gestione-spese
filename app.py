import streamlit as st
import pandas as pd

# File e fogli
EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"
FOGLIO_RIEPILOGO = "Riepilogo 2025"
FOGLIO_DASHBOARD = "Dashboard 2025"

# Categorie dei tag
CATEGORIE_TAG = {
    "Entrate": ["Stipendio", "Bonus", "Altre Entrate"],
    "Uscite Necessarie": ["Affitto", "Bollette", "Spesa", "Abbonamenti"],
    "Uscite Variabili": ["Ristorante", "Viaggi", "Shopping", "Altro"]
}

# Caricamento dati spese dettagliate
@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE, skiprows=1)
    df = df.dropna(subset=["Valore", "Tag"])
    df = df[~df["Valore"].astype(str).str.startswith("Totale")]

    def categoria_per_tag(tag):
        for cat, tag_list in CATEGORIE_TAG.items():
            if tag in tag_list:
                return cat
        return "Non classificato"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    return df

# Caricamento riepilogo
@st.cache_data
def carica_riepilogo():
    df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_RIEPILOGO)
    return df

# Caricamento dashboard
@st.cache_data
def carica_dashboard():
    df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_DASHBOARD)
    return df

# Sidebar per selezione vista
vista = st.sidebar.selectbox("Seleziona Vista", ["📊 Dashboard", "📂 Riepilogo Mensile", "🧾 Spese Dettagliate"])

# Vista: Dashboard
if vista == "📊 Dashboard":
    st.title("📊 Dashboard Mensile")

    df = carica_dashboard()

    # Mantieni solo le colonne fino a "Total"
    if "Total" in df.columns:
        col_index = df.columns.get_loc("Total") + 1
        df = df.iloc[:, :col_index]

    # Formatto tutti i valori numerici in euro
    def formatta_euro(val):
        if isinstance(val, (int, float)):
            return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return val

    df_format = df.applymap(formatta_euro)

    # Mostra la tabella senza indici
    st.dataframe(df_format, hide_index=True)

# Vista: Riepilogo Mensile
elif vista == "📂 Riepilogo Mensile":
    st.title("📂 Riepilogo Mensile per Tag")

    df = carica_riepilogo()

    # Formatto in euro
    def formatta_euro(val):
        if isinstance(val, (int, float)):
            return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return val

    df_format = df.applymap(formatta_euro)
    st.dataframe(df_format, hide_index=True)

# Vista: Spese Dettagliate
elif vista == "🧾 Spese Dettagliate":
    st.title("🧾 Spese Dettagliate")

    df = carica_spese()

    # Formatto in euro
    def formatta_euro(val):
        if isinstance(val, (int, float)):
            return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return val

    df["Valore"] = df["Valore"].apply(formatta_euro)

    st.dataframe(df, hide_index=True)
