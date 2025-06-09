import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"

# === FUNZIONI ===

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data

def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Valore", "Tag"])
    df = df.reset_index(drop=True)
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)

    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    return df

# === DASHBOARD AUTOMATICA ===
def calcola_dashboard(df_spese):
    mesi = [col for col in df_spese.columns if col not in ["Testo", "Valore", "Tag", "Categoria"]]
    df_long = pd.melt(df_spese, id_vars=["Testo", "Valore", "Tag", "Categoria"],
                      var_name="Mese", value_name="Attivo")
    df_long = df_long[df_long["Attivo"] == "x"]

    df_mensile = df_long.groupby(["Mese", "Categoria"]).agg({"Valore": "sum"}).reset_index()
    pivot = df_mensile.pivot(index="Categoria", columns="Mese", values="Valore").fillna(0)

    # Calcolo risparmio mese
    entrate = pivot.loc["Entrate"] if "Entrate" in pivot.index else 0
    uscite_nec = pivot.loc["Uscite necessarie"] if "Uscite necessarie" in pivot.index else 0
    uscite_var = pivot.loc["Uscite variabili"] if "Uscite variabili" in pivot.index else 0
    risparmio_mese = entrate - uscite_nec - uscite_var

    pivot.loc["Risparmio mese"] = risparmio_mese
    pivot.loc["Risparmio cumulato"] = risparmio_mese.cumsum()

    pivot["Total"] = pivot.sum(axis=1)

    return pivot

# === INTERFACCIA ===
st.set_page_config(page_title="Gestione Spese", layout="wide")
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Dashboard"])

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

elif vista == "Dashboard":
    st.title("📈 Dashboard")
    df_spese = carica_spese()
    df_dash = calcola_dashboard(df_spese)

    df_formattato = df_dash.copy().reset_index().rename(columns={"index": "Voce"})
    for col in df_formattato.columns[1:]:
        df_formattato[col] = df_formattato[col].apply(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_formattato, use_container_width=True, hide_index=True)

    categorie = [c for c in ["Entrate", "Uscite necessarie", "Uscite variabili", "Risparmio mese", "Risparmio cumulato"] if c in df_dash.index]
    if categorie:
        df_valori = df_dash.loc[categorie].drop(columns=["Total"])
        df_valori = df_valori.transpose()

        st.subheader("📊 Andamento mensile per categoria")
        fig, ax = plt.subplots(figsize=(12, 6))
        df_valori.plot(kind="bar", ax=ax)
        ax.set_ylabel("Importo (€)")
        ax.set_xlabel("Mese")
        ax.set_title("Entrate, Uscite e Risparmi per mese")
        ax.legend(title="Categoria")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("⚠️ Nessuna categoria trovata per il grafico.")
