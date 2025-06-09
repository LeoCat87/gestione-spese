import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# === CONFIGURAZIONE ===
EXCEL_PATH = "Spese_Leo.xlsx"
SHEET_NAME = "Spese 2025"

# === FUNZIONE DI CARICAMENTO E RIORGANIZZAZIONE ===
@st.cache_data
def carica_spese():
    df_raw = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, header=[0, 1])
    dati = []

    for mese in df_raw.columns.levels[0]:
        if mese is None or pd.isna(mese):
            continue
        try:
            blocco = df_raw[mese][['Testo', 'Valore', 'Tag']].copy()
            blocco.columns = ['Testo', 'Importo', 'Tag']
            blocco["Mese"] = mese
            dati.append(blocco)
        except KeyError:
            continue

    df = pd.concat(dati, ignore_index=True)
    df = df.dropna(subset=["Importo"])
    return df

# === MAPPATURA CATEGORIE ===
MAPPATURA = {
    "Spesa casa": ["Affitto", "Mutuo", "Condominio", "Manutenzione casa"],
    "Spesa auto": ["Carburante", "Assicurazione", "Manutenzione auto"],
    "Spesa personale": ["Abbigliamento", "Parrucchiere", "Cura personale"],
    "Spesa tempo libero": ["Ristoranti", "Cinema", "Viaggi"],
    "Altre spese": []
}

def assegna_macrocategoria(tag):
    for macro, tags in MAPPATURA.items():
        if tag in tags:
            return macro
    return "Altre spese"

# === APP STREAMLIT ===
st.title("Dashboard Spese Personali")

spese_df = carica_spese()

if "Tag" in spese_df.columns and "Importo" in spese_df.columns:
    spese_df["Macrocategoria"] = spese_df["Tag"].apply(assegna_macrocategoria)

    # Totale per macrocategoria
    totali_macro = spese_df.groupby("Macrocategoria")["Importo"].sum()

    # Totale per mese
    totali_mese = spese_df.groupby("Mese")["Importo"].sum()

    # === GRAFICI ===
    st.subheader("Spese per Macrocategoria")
    fig1, ax1 = plt.subplots()
    ax1.pie(totali_macro, labels=totali_macro.index, autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)

    st.subheader("Spese mensili")
    fig2, ax2 = plt.subplots()
    totali_mese.plot(kind="bar", ax=ax2)
    ax2.set_ylabel("Euro")
    st.pyplot(fig2)

    # === TABELLA ===
    st.subheader("Dettaglio Spese")
    st.dataframe(spese_df)

else:
    st.error("Il file Excel deve contenere almeno le colonne 'Tag' e 'Valore'.")
