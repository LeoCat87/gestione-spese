import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese"

@st.cache_data
def carica_spese():
    # Carica i dati
    raw_df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE, header=[0, 1])
    
    # Riorganizza i dati
    mesi = raw_df.columns.levels[0]
    dati = []

    for mese in mesi:
        if mese not in raw_df.columns:
            continue
        blocco = raw_df[mese]
        blocco = blocco.dropna(how='all')  # rimuove righe completamente vuote
        blocco = blocco.rename(columns={"Testo": "Testo", "Valore": "Importo", "Tag": "Tag"})
        blocco["Mese"] = mese
        dati.append(blocco)

    df_finale = pd.concat(dati, ignore_index=True)
    df_finale = df_finale.dropna(subset=["Importo", "Tag"])
    return df_finale

# Mappa tag a macrocategorie
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

# App Streamlit
st.title("Dashboard Spese Personali")

df = carica_spese()

if "Tag" in df.columns and "Importo" in df.columns:
    df["Macrocategoria"] = df["Tag"].apply(assegna_macrocategoria)

    # Totali per macrocategoria
    totali_macro = df.groupby("Macrocategoria")["Importo"].sum()

    # Totali per mese
    totali_mese = df.groupby("Mese")["Importo"].sum()

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

    st.subheader("Dettaglio Spese")
    st.dataframe(df)
else:
    st.error("Il file non contiene colonne 'Tag' e 'Importo'.")
