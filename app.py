import streamlit as st
import pandas as pd

EXCEL_PATH = "Spese_Leo.xlsx"
FOGLIO_SPESE = "Spese"

@st.cache_data
def carica_spese():
    return pd.read_excel(EXCEL_PATH, sheet_name=FOGLIO_SPESE)

def salva_spese(df):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=FOGLIO_SPESE, index=False)

st.title("💰 Gestione Spese Personali")

spese_df = carica_spese()
st.subheader("📊 Tabella delle Spese")
st.dataframe(spese_df)

st.subheader("➕ Aggiungi una nuova spesa")

with st.form("aggiungi_spesa"):
    nuova_data = st.date_input("Data")
    nuova_categoria = st.text_input("Categoria")
    nuovo_importo = st.number_input("Importo", min_value=0.0, step=0.01)
    nuova_descrizione = st.text_input("Descrizione")
    aggiungi = st.form_submit_button("Aggiungi")

if aggiungi:
    nuova_riga = {
        "Data": nuova_data,
        "Categoria": nuova_categoria,
        "Importo": nuovo_importo,
        "Descrizione": nuova_descrizione
    }
    spese_df = pd.concat([spese_df, pd.DataFrame([nuova_riga])], ignore_index=True)
    st.success("✅ Spesa aggiunta. Scarica il file aggiornato sotto.")

    # Esportazione file modificato
    st.download_button(
        label="📥 Scarica Excel aggiornato",
        data=spese_df.to_excel(index=False, engine="openpyxl"),
        file_name="spese_aggiornate.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
