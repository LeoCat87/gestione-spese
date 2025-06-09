import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"

# Mappatura dei tag a macrocategorie
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

@st.cache_data
def carica_spese():
    # Leggi il file con intestazioni multilivello (riga 1 = mese, riga 2 = campo)
    raw_df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE, header=[0, 1])
    
    # Pulisce i nomi di mese e campi
    raw_df.columns = pd.MultiIndex.from_tuples([
        (str(col[0]).strip(), str(col[1]).strip()) for col in raw_df.columns
    ])

    dati = []
    for mese in raw_df.columns.levels[0]:
        if mese.strip() == "" or mese == "nan":
            continue
        try:
            blocco = raw_df[mese][['Testo', 'Valore', 'Tag']].copy()
            blocco = blocco.dropna(subset=['Valore'])  # Solo spese con valore
            blocco['Mese'] = mese
            dati.append(blocco)
        except KeyError:
            continue

    if dati:
        df = pd.concat(dati, ignore_index=True)
        df.rename(columns={'Valore': 'Importo'}, inplace=True)
        df['Macrocategoria'] = df['Tag'].apply(assegna_macrocategoria)
        return df
    else:
        return pd.DataFrame()

# App principale
st.title("Dashboard Spese Personali")

df = carica_spese()

if df.empty:
    st.error("Nessun dato caricato. Verifica il file Excel.")
else:
    # Grafico a torta: spese per macrocategoria
    st.subheader("Distribuzione per Macrocategoria")
    totali_macro = df.groupby("Macrocategoria")["Importo"].sum()
    fig1, ax1 = plt.subplots()
    ax1.pie(totali_macro, labels=totali_macro.index, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)

    # Grafico a barre: spese mensili
    st.subheader("Spese Mensili")
    totali_mese = df.groupby("Mese")["Importo"].sum()
    fig2, ax2 = plt.subplots()
    totali_mese.plot(kind="bar", ax=ax2)
    ax2.set_ylabel("Euro")
    st.pyplot(fig2)

    # Tabella
    st.subheader("Dettaglio Spese")
    st.dataframe(df)
