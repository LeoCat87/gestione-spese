import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
import io
from fpdf import FPDF

st.set_page_config(page_title="Gestione Spese", layout="wide")

# === FUNZIONI ESPORTAZIONE ===
def esporta_excel(df, nome_file="report.xlsx"):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button(
        label="📅 Scarica Excel",
        data=buffer.getvalue(),
        file_name=nome_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def esporta_pdf(df, nome_file="report.pdf", titolo="Report"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, titolo, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)

    col_widths = [40] + [30] * (len(df.columns) - 1)
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 10, str(col)[:15], border=1)
    pdf.ln()

    for _, row in df.iterrows():
        for i, col in enumerate(df.columns):
            testo = str(row[col])[:20]
            pdf.cell(col_widths[i], 10, testo, border=1)
        pdf.ln()

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    st.download_button(
        label="🪾 Scarica PDF",
        data=pdf_bytes,
        file_name=nome_file,
        mime="application/pdf"
    )

# === CONFIGURAZIONE ===
GDRIVE_FILE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
EXCEL_PATH = "Spese_App.xlsx"

@st.cache_data
def scarica_excel_da_drive():
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    gdown.download(url, EXCEL_PATH, quiet=True)
scarica_excel_da_drive()

@st.cache_data
def carica_spese():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese Leo", header=[1])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(subset=["Valore", "Tag"])
    df = df.reset_index(drop=True)
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce").fillna(0)
    def categoria_per_tag(tag):
        if tag in ["Stipendio", "Entrate extra"]:
            return "Entrate"
        elif tag in ["Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione"]:
            return "Uscite necessarie"
        else:
            return "Uscite variabili"
    df["Categoria"] = df["Tag"].apply(categoria_per_tag)
    return df

@st.cache_data
def carica_riepilogo():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo Leo", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

# === VISTA: SPESE DETTAGLIATE ===
if vista == "Spese dettagliate":
    st.title("📌 Spese Dettagliate")
    df_spese = carica_spese()
    col1, col2 = st.columns(2)
    with col1:
        categoria_sel = st.selectbox("Filtra per categoria:", ["Tutte"] + sorted(df_spese["Categoria"].unique()))
    with col2:
        tag_sel = st.selectbox("Filtra per tag:", ["Tutti"] + sorted(df_spese["Tag"].unique()))

    df_filtrato = df_spese.copy()
    if categoria_sel != "Tutte":
        df_filtrato = df_filtrato[df_filtrato["Categoria"] == categoria_sel]
    if tag_sel != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["Tag"] == tag_sel]

    df_mostrato = df_filtrato.drop(columns=["Categoria"])
    df_mostrato["Valore"] = df_mostrato["Valore"].map(formatta_euro)

    st.dataframe(df_mostrato, use_container_width=True)
    esporta_excel(df_filtrato.drop(columns=["Categoria"]), nome_file="Spese_dettagliate.xlsx")
    esporta_pdf(df_filtrato.drop(columns=["Categoria"]), nome_file="Spese_dettagliate.pdf", titolo="Spese Dettagliate")

# === VISTA: RIEPILOGO MENSILE ===
elif vista == "Riepilogo mensile":
    st.title("📊 Riepilogo Mensile per Tag")
    df_spese = carica_spese()
    df_pivot = df_spese.pivot_table(index="Tag", columns="Categoria", values="Valore", aggfunc="sum", fill_value=0)
    df_riepilogo = df_spese.groupby(["Tag"])["Valore"].sum().reset_index()
    df_export = df_spese.groupby(["Tag", "Categoria"])["Valore"].sum().reset_index()
    df_export = df_export.pivot(index="Tag", columns="Categoria", values="Valore").fillna(0).reset_index()
    st.dataframe(df_export, use_container_width=True, hide_index=True)
    esporta_excel(df_export, nome_file="Riepilogo_mensile.xlsx")
    esporta_pdf(df_export, nome_file="Riepilogo_mensile.pdf", titolo="Riepilogo Mensile")

# === VISTA: DASHBOARD ===
elif vista == "Dashboard":
    st.title("📈 Dashboard")
    df_spese = carica_spese()
    df_pivot = df_spese.groupby("Categoria")["Valore"].sum().reset_index()
    df_tabella = df_pivot.copy()
    df_tabella["Valore"] = df_tabella["Valore"].map(formatta_euro)
    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_tabella, use_container_width=True, hide_index=True)
    esporta_excel(df_pivot, nome_file="Dashboard_finanziaria.xlsx")
    esporta_pdf(df_pivot, nome_file="Dashboard_finanziaria.pdf", titolo="Dashboard Finanziaria")

    st.subheader("📈 Grafico per Categoria")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_pivot["Categoria"], df_pivot["Valore"])
    ax.set_ylabel("Valore (€)")
    ax.set_xlabel("Categoria")
    ax.set_title("Distribuzione per Categoria")
    st.pyplot(fig)
