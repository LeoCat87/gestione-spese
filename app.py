import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"

# Mappa tag a categorie principali
CATEGORIE = {
    "Entrate": ["Stipendio", "Entrate extra"],
    "Uscite Necessarie": ["Affitto", "Mutuo", "Condominio", "Manutenzione casa", "Carburante", "Assicurazione", "Spesa alimentare", "Utenze"],
    "Uscite Variabili": ["Abbigliamento", "Parrucchiere", "Cura personale", "Ristoranti", "Cinema", "Viaggi", "Tempo libero"]
}

def categoria_per_tag(tag):
    for cat, tags in CATEGORIE.items():
        if tag in tags:
            return cat
    return "Altro"

@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    df["Mese"] = pd.to_datetime(df["Data"]).dt.strftime("%B")
    return df

@st.cache_data
def carica_riepilogo():
    return pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)

@st.cache_data
def carica_dashboard():
    return pd.read_excel(EXCEL_PATH, sheet_name="Dashboard", index_col=0)

# Sidebar
vista = st.sidebar.radio("Seleziona vista", ["📒 Spese dettagliate", "📊 Riepilogo mensile", "📈 Dashboard aggregata"])

# Vista 1: Spese dettagliate
if vista == "📒 Spese dettagliate":
    st.title("📒 Spese Dettagliate")
    df = carica_spese()
    mesi = sorted(df["Mese"].unique(), key=lambda m: pd.to_datetime(m, format="%B").month)
    mese_sel = st.selectbox("Seleziona mese", mesi)
    df_mese = df[df["Mese"] == mese_sel]
    st.dataframe(df_mese[["Data", "Descrizione", "Importo", "Tag", "Categoria"]])
    st.bar_chart(df_mese.groupby("Categoria")["Importo"].sum())

# Vista 2: Riepilogo mensile per Tag
elif vista == "📊 Riepilogo mensile":
    st.title("📊 Riepilogo per Tag")
    riepilogo = carica_riepilogo()
    st.dataframe(riepilogo.style.format("{:.2f}"))
    mese_sel = st.selectbox("Seleziona mese", riepilogo.columns)
    st.bar_chart(riepilogo[mese_sel])

# Vista 3: Dashboard aggregata
elif vista == "📈 Dashboard aggregata":
    st.title("📈 Dashboard Mensile")
    dashboard = carica_dashboard()
    st.dataframe(dashboard.style.format("{:.2f}"))

    # Grafico Risparmio Mensile
    fig, ax = plt.subplots()
    dashboard["Risparmio"].plot(kind="bar", ax=ax, color="green")
    ax.set_ylabel("Risparmio (€)")
    ax.set_title("Risparmio Mensile")
    st.pyplot(fig)

    # Grafico Risparmio Cumulato
    fig2, ax2 = plt.subplots()
    dashboard["Risparmio Cumulato"].plot(kind="line", marker="o", ax=ax2, color="blue")
    ax2.set_ylabel("Risparmio Cumulato (€)")
    ax2.set_title("Andamento Risparmio Cumulato")
    st.pyplot(fig2)
