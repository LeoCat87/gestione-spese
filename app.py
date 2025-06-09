import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
import os

FILE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
EXCEL_PATH = "Spese_Leo.xlsx"

if not os.path.exists(EXCEL_PATH):
    url = f"https://drive.google.com/uc?id={FILE_ID}"
    gdown.download(url, EXCEL_PATH, quiet=False)

# === FUNZIONI DI CARICAMENTO ===

@st.cache_data
def carica_spese():
    df_raw = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
    mesi_riga = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=None).iloc[0]
    mesi = mesi_riga[mesi_riga.notna()].tolist()[2:]  # esclude prime colonne (Testo, Tag)

    records = []
    for i, row in df_raw.iterrows():
        for idx, mese in enumerate(mesi):
            col = df_raw.columns[2 + idx]
            valore = row[col]
            if pd.notna(valore) and valore != 0:
                records.append({
                    "Testo": row["Testo"],
                    "Tag": row["Tag"],
                    "Mese": mese,
                    "Valore": valore
                })
    df = pd.DataFrame(records)

    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"

    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)
    return df

@st.cache_data
def carica_riepilogo():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def calcola_dashboard(df_spese):
    categorie_da_usare = ["Entrate", "Uscite necessarie", "Uscite variabili"]
    pivot = df_spese[df_spese["Categoria"].isin(categorie_da_usare)]
    pivot = pivot.groupby(["Categoria", "Mese"])["Valore"].sum().unstack(fill_value=0)

    if pivot.empty:
        return pd.DataFrame(columns=["Voce"])

    for cat in categorie_da_usare:
        if cat not in pivot.index:
            pivot.loc[cat] = 0

    risparmio_mese = pivot.loc["Entrate"] - pivot.loc["Uscite necessarie"] - pivot.loc["Uscite variabili"]
    pivot.loc["Risparmio mese"] = risparmio_mese
    pivot.loc["Risparmio cumulato"] = risparmio_mese.cumsum()
    pivot["Total"] = pivot.sum(axis=1)
    return pivot

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===

st.set_page_config(page_title="Gestione Spese", layout="wide")
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

# === VISTA 1: SPESE DETTAGLIATE ===

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

# === VISTA 2: RIEPILOGO MENSILE ===

elif vista == "Riepilogo mensile":
    st.title("📊 Riepilogo Mensile per Tag")
    df_riepilogo = carica_riepilogo()
    df_formattato = df_riepilogo.applymap(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)
    st.dataframe(df_formattato, use_container_width=True, hide_index=True)

# === VISTA 3: DASHBOARD ===

elif vista == "Dashboard":
    st.title("📈 Dashboard")
    df_spese = carica_spese()
    df_dash = calcola_dashboard(df_spese)

    if df_dash.empty:
        st.warning("⚠️ Nessun dato disponibile per generare la dashboard.")
    else:
        df_formattato = df_dash.copy().reset_index().rename(columns={"index": "Voce"})

        for col in df_formattato.columns[1:]:
            df_formattato[col] = df_formattato[col].apply(
                lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x
            )

        st.subheader("📊 Tabella riepilogo")
        st.dataframe(df_formattato, use_container_width=True, hide_index=True)

        categorie_attese = [
            "Entrate", "Uscite necessarie", "Uscite variabili",
            "Risparmio mese", "Risparmio cumulato"
        ]
        categorie_presenti = [cat for cat in categorie_attese if cat in df_dash.index]

        df_valori = df_dash.drop(columns=["Total"])
        df_valori = df_valori.loc[categorie_presenti]
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
