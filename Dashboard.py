import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"

@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE)
    # Mantieni solo le colonne essenziali
    colonne_necessarie = ["Data", "Tag", "Importo"]
    df = df[[col for col in colonne_necessarie if col in df.columns]].copy()

    # Conversioni sicure
    df["Importo"] = pd.to_numeric(df["Importo"], errors="coerce")
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    return df.dropna(subset=["Importo", "Tag"])

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

try:
    df = carica_spese()

    # Applica macrocategoria
    df["Macrocategoria"] = df["Tag"].apply(assegna_macrocategoria)

    # Aggiungi colonna "Mese"
    if "Data" in df.columns:
        df["Mese"] = df["Data"].dt.to_period("M")
        totali_mese = df.groupby("Mese")["Importo"].sum()
    else:
        totali_mese = pd.Series(dtype=float)
        st.warning("Colonna 'Data' mancante o non valida.")

    # Totali per macrocategoria
    totali_macro = df.groupby("Macrocategoria")["Importo"].sum()

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

    # Tabella finale
    st.subheader("Dettaglio Spese")
    st.dataframe(df[["Data", "Tag", "Importo", "Macrocategoria"]])

except Exception as e:
    st.error(f"Errore durante l'e
