import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Gestione Spese", layout="wide")

GOOGLE_DRIVE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"

@st.cache_data(ttl=600)
def carica_file_excel():
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DRIVE_ID}/export?format=xlsx"
    xls = pd.ExcelFile(url)
    return xls

xls = carica_file_excel()

# Carico il foglio Spese 2025
df_spese = pd.read_excel(xls, sheet_name="Spese 2025")

# Carico il foglio Dashboard 2025 (usato per la dashboard)
df_dash = pd.read_excel(xls, sheet_name="Dashboard 2025")

st.title("Gestione Spese")

# Vista spese dettagliate (mostra direttamente il foglio Spese 2025)
st.subheader("Spese dettagliate")
st.dataframe(df_spese)

# Vista Dashboard (usa il foglio Dashboard 2025 come dati)
st.subheader("Dashboard")
st.dataframe(df_dash.style.format("{:,.2f} €"))

# Grafico da df_dash (usando colonne e righe così come sono nel foglio Dashboard 2025)
fig, ax = plt.subplots(figsize=(12, 6))

# Assumo che la prima colonna di df_dash contenga le categorie (Entrate, Uscite, etc.)
categorie = df_dash.iloc[:, 0]
mesi = df_dash.columns[1:]  # le colonne successive sono mesi

for i, categoria in enumerate(categorie):
    ax.plot(mesi, df_dash.iloc[i, 1:], marker='o', label=categoria)

ax.set_title("Dashboard Spese")
ax.set_ylabel("Euro")
ax.legend()
plt.xticks(rotation=45)
st.pyplot(fig)
