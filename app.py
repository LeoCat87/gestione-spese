import streamlit as st
import pandas as pd

EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"

# Mappatura tag → categoria
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
    # Carica Excel
    df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE, header=[0, 1])
    
    # Crea dataframe unificato partendo da struttura mensile (multi colonna)
    dati = []
    for mese in df.columns.levels[0]:
        if pd.isna(mese):  # Salta colonne vuote
            continue
        try:
            col_mese = df[mese]
            blocco = col_mese[['Testo', 'Valore', 'Tag']].dropna(how='all')
            blocco = blocco.rename(columns={"Testo": "Testo", "Valore": "Importo", "Tag": "Tag"})
            blocco["Mese"] = mese
            dati.append(blocco)
        except KeyError:
            continue

    completo = pd.concat(dati, ignore_index=True)
    completo = completo.dropna(subset=["Importo"])
    completo["Categoria"] = completo["Tag"].apply(categoria_per_tag)
    return completo

# App
st.title("📊 Spese dettagliate")

df = carica_spese()

st.dataframe(df)

# Totale per categoria
st.subheader("Totali per Categoria")
totali_categoria = df.groupby("Categoria")["Importo"].sum().reset_index()
st.dataframe(totali_categoria)

# Filtro per mese (opzionale)
mesi_disponibili = df["Mese"].unique()
mese_sel = st.selectbox("Filtra per mese:", sorted(mesi_disponibili))
df_filtrato = df[df["Mese"] == mese_sel]

st.subheader(f"Spese dettagliate per {mese_sel}")
st.dataframe(df_filtrato)
