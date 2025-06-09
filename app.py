import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese 2025"

# Mappa tag → macrocategoria
MAPPATURA = {
    "Spesa casa": ["Affitto", "Mutuo", "Condominio", "Manutenzione casa"],
    "Spesa auto": ["Carburante", "Assicurazione", "Manutenzione auto"],
    "Spesa personale": ["Abbigliamento", "Parrucchiere", "Cura personale"],
    "Spesa tempo libero": ["Ristoranti", "Cinema", "Viaggi"],
    "Altre spese": []
}

def assegna_macrocategoria(tag):
    tag_normalizzato = str(tag).lower().strip()
    for macro, tags in MAPPATURA.items():
        for t in tags:
            if t.lower() in tag_normalizzato:
                return macro
    return "Altre spese"

@st.cache_data
def carica_spese():
    raw_df = pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE, header=[0, 1])
    spese_lista = []

    for mese in raw_df.columns.levels[0]:
        if not all(col in raw_df[mese].columns for col in ["Testo", "Valore", "Tag"]):
            continue  # ignora colonne incomplete

        blocco = raw_df[mese][["Testo", "Valore", "Tag"]].dropna(how="all")
        blocco.columns = ["Testo", "Importo", "Tag"]
        blocco["Mese"] = mese
        spese_lista.append(blocco)

    df = pd.concat(spese_lista, ignore_index=True)
    df["Macrocategoria"] = df["Tag"].apply(assegna_macrocategoria)
    return df

# App
st.title("Dashboard Spese Personali")
df = carica_spese()

# Totali per macrocategoria
totali_macro = df.groupby("Macrocategoria")["Importo"].sum()

# Totali per mese
totali_mese = df.groupby("Mese")["Importo"].sum()

# Grafico torta
st.subheader("Spese per Macrocategoria")
fig1, ax1 = plt.subplots()
ax1.pie(totali_macro, labels=totali_macro.index, autopct="%1.1f%%", startangle=90)
ax1.axis("equal")
st.pyplot(fig1)

# Grafico barre
st.subheader("Spese Mensili")
fig2, ax2 = plt.subplots()
totali_mese.plot(kind="bar", ax=ax2)
ax2.set_ylabel("Euro")
st.pyplot(fig2)

# Tabella
st.subheader("Dettaglio Spese")
st.dataframe(df)
