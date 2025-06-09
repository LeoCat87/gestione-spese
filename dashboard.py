
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Percorso file Excel
EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"

# Carica e pulisce i dati
@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE)
    # Rimuove colonne senza intestazione
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    # Rimuove colonne completamente vuote
    df = df.dropna(axis=1, how='all')
    # Rimuove righe completamente vuote
    df = df.dropna(how='all')
    return df

# Mapping tag → macrocategorie
MAPPATURA = {
    "Spesa casa": ["Affitto", "Mutuo", "Condominio", "Manutenzione casa"],
    "Spesa auto": ["Carburante", "Assicurazione", "Manutenzione auto"],
    "Spesa personale": ["Abbigliamento", "Parrucchiere", "Cura personale"],
    "Spesa tempo libero": ["Ristoranti", "Cinema", "Viaggi"],
    "Altre spese": []  # tutto il resto va qui
}

def assegna_macrocategoria(tag):
    for macro, tags in MAPPATURA.items():
        if tag in tags:
            return macro
    return "Altre spese"

# App principale
st.title("Dashboard Spese Personali")

try:
    spese_df = carica_spese()

    # Pre-elabora dati
    if "Tag" in spese_df.columns:
        spese_df["Macrocategoria"] = spese_df["Tag"].apply(assegna_macrocategoria)
    else:
        spese_df["Macrocategoria"] = "Altre spese"

    # Totale per macrocategoria
    totali_macro = spese_df.groupby("Macrocategoria")["Importo"].sum()

    # Totale per mese
    if "Data" in spese_df.columns:
        spese_df["Mese"] = pd.to_datetime(spese_df["Data"], errors='coerce').dt.to_period("M")
        totali_mese = spese_df.groupby("Mese")["Importo"].sum()
    else:
        st.warning("Colonna 'Data' non trovata nel file.")
        totali_mese = pd.Series(dtype=float)

    # Grafico a torta
    st.subheader("Spese per Macrocategoria")
    fig1, ax1 = plt.subplots()
    ax1.pie(totali_macro, labels=totali_macro.index, autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)

    # Grafico a barre
    st.subheader("Spese mensili")
    if not totali_mese.empty:
        fig2, ax2 = plt.subplots()
        totali_mese.plot(kind="bar", ax=ax2)
        ax2.set_ylabel("Euro")
        st.pyplot(fig2)

    # Tabella riepilogativa
    st.subheader("Dettaglio Spese")
    st.dataframe(spese_df)

except Exception as e:
    st.error(f"Errore nel caricamento dati: {e}")
