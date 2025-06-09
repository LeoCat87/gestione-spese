import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"

@st.cache_data
def carica_spese():
    # Carica il file con multi-header
    raw_df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE, header=[0, 1])
    
    dati = []

    for mese in raw_df.columns.levels[0]:
        if mese == '' or ('Valore' not in raw_df[mese]):
            continue
        blocco = raw_df[mese][['Testo', 'Valore', 'Tag']].copy()
        blocco.columns = ['Testo', 'Importo', 'Tag']
        blocco['Mese'] = mese
        dati.append(blocco)

    df_finale = pd.concat(dati, ignore_index=True)
    df_finale = df_finale.dropna(subset=["Importo", "Tag"])
    df_finale = df_finale[df_finale["Importo"].apply(lambda x: isinstance(x, (int, float)))]
    
    return df_finale

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
    st.dataframe(df.reset_index(drop=True))
else:
    st.error("Il file non contiene le colonne 'Tag' e 'Importo'.")
