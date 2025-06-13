import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from openpyxl import load_workbook

st.set_page_config(layout="wide")

EXCEL_FILE = "Spese_App.xlsx"
FOGLIO_SPESE = "Spese Leo"
FOGLIO_RIEPILOGO = "Riepilogo Leo"

mesi_ordinati = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

mappa_macrocategorie = {
    "Entrate": ["Stipendio", "Altre entrate"],
    "Uscite necessarie": ["Affitto", "Bolletta", "Spesa", "Abbonamenti"],
    "Uscite variabili": ["Ristorante", "Shopping", "Svago"],
    "Risparmio mese": [],  # Calcolato
    "Risparmio cumulato": []  # Calcolato
}

def carica_spese():
    df_raw = pd.read_excel(EXCEL_FILE, sheet_name=FOGLIO_SPESE, header=1, engine="openpyxl")
    mesi = df_raw.columns[1:]
    records = []
    for mese in mesi:
        df_mese = df_raw[["Testo", "Valore", "Tag"]].copy()
        df_mese["Mese"] = mese
        records.append(df_mese)
    df = pd.concat(records, ignore_index=True)
    df = df.dropna(subset=["Testo", "Valore", "Tag"])
    return df

def salva_spese_formattato(df):
    mesi = df["Mese"].unique()
    writer = pd.ExcelWriter(EXCEL_FILE, engine="openpyxl")
    wb = load_workbook(EXCEL_FILE)
    if FOGLIO_SPESE in wb.sheetnames:
        wb.remove(wb[FOGLIO_SPESE])
    wb.create_sheet(FOGLIO_SPESE)
    writer.book = wb
    writer.sheets = {ws.title: ws for ws in wb.worksheets}
    tutti_i_mesi = mesi_ordinati
    righe = []
    for mese in tutti_i_mesi:
        df_mese = df[df["Mese"] == mese]
        righe.extend(df_mese[["Testo", "Valore", "Tag"]].values.tolist())
    df_output = pd.DataFrame(righe, columns=["Testo", "Valore", "Tag"])
    df_output.to_excel(writer, sheet_name=FOGLIO_SPESE, index=False, startrow=1)
    writer.close()
    st.cache_data.clear()

def vista_riepilogo():
    st.header("📊 Riepilogo mensile")
    df = carica_spese()
    df_riep_cat = pd.pivot_table(df, index="Tag", columns="Mese", values="Valore", aggfunc="sum", fill_value=0)
    for mese in mesi_ordinati:
        if mese not in df_riep_cat.columns:
            df_riep_cat[mese] = 0
    df_riep_cat = df_riep_cat[mesi_ordinati]
    df_riep_cat["Totale"] = df_riep_cat.sum(axis=1)
    st.dataframe(df_riep_cat.style.format("{:.2f}"), use_container_width=True)

def vista_dashboard():
    st.header("📈 Dashboard")
    df = carica_spese()
    df_riep = df.groupby(["Tag", "Mese"])["Valore"].sum().reset_index()
    df_macrocategorie = pd.DataFrame(0, index=list(mappa_macrocategorie.keys()), columns=mesi_ordinati)
    for categoria, tags in mappa_macrocategorie.items():
        df_filtrato = df_riep[df_riep["Tag"].isin(tags)]
        df_grouped = df_filtrato.groupby("Mese")["Valore"].sum()
        df_grouped = df_grouped.reindex(mesi_ordinati, fill_value=0)
        df_macrocategorie.loc[categoria] = df_grouped
    df_macrocategorie.loc["Risparmio mese"] = df_macrocategorie.loc["Entrate"] - df_macrocategorie.loc["Uscite necessarie"] - df_macrocategorie.loc["Uscite variabili"]
    df_macrocategorie.loc["Risparmio cumulato"] = df_macrocategorie.loc["Risparmio mese"].cumsum()
    df_macrocategorie["Total"] = df_macrocategorie.sum(axis=1)
    st.dataframe(df_macrocategorie.style.format("{:.2f}"), use_container_width=True)
    df_plot = df_macrocategorie.T.reset_index().rename(columns={"index": "Mese"})
    df_plot = df_plot[df_plot["Mese"].isin(mesi_ordinati)]
    df_plot.set_index("Mese", inplace=True)
    df_plot[["Entrate", "Uscite necessarie", "Uscite variabili", "Risparmio mese"]].plot(kind="bar", figsize=(12, 6))
    plt.ylabel("Valore in €")
    st.pyplot(plt.gcf())
    plt.clf()
    df_plot[["Risparmio cumulato"]].plot(kind="line", marker="o", figsize=(12, 4))
    plt.ylabel("Risparmio cumulato")
    st.pyplot(plt.gcf())
    plt.clf()

def main():
    vista = st.sidebar.selectbox("Seleziona vista", ["Riepilogo mensile", "Dashboard"])
    if vista == "Riepilogo mensile":
        vista_riepilogo()
    elif vista == "Dashboard":
        vista_dashboard()

if __name__ == "__main__":
    main()
