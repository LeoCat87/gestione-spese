import streamlit as st
import pandas as pd
import gdown
import openpyxl
import matplotlib.pyplot as plt
import os
import io

st.set_page_config(page_title="Gestione Spese", layout="wide")

# === CONFIGURAZIONE ===
GDRIVE_FILE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
EXCEL_FILE = "Spese_App.xlsx"

# Scarica il file Excel da Google Drive
@st.cache_data
def scarica_excel_da_drive():
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    gdown.download(url, EXCEL_FILE, quiet=True)

scarica_excel_da_drive()

# === FUNZIONI DI CARICAMENTO ===
@st.cache_data
def carica_spese():
    df_raw = pd.read_excel(EXCEL_FILE, sheet_name="Spese Leo", header=1)
    df_raw = df_raw.loc[:, ~df_raw.columns.str.contains("^Unnamed")]

    mesi = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]

    records = []

    for i, mese in enumerate(mesi):
        col_base = i * 3
        if col_base + 2 < len(df_raw.columns):
            sotto_df = df_raw.iloc[:, col_base:col_base+3].copy()
            sotto_df.columns = ["Testo", "Valore", "Tag"]
            sotto_df = sotto_df.dropna(how="all", subset=["Valore", "Testo", "Tag"])
            sotto_df["Mese"] = mese.lower()
            sotto_df["Tag"] = sotto_df["Tag"].fillna('').astype(str).str.strip().str.capitalize()
            sotto_df["Testo"] = sotto_df["Testo"].fillna('').astype(str).str.strip()
            sotto_df["Valore"] = pd.to_numeric(sotto_df["Valore"], errors="coerce")
            records.append(sotto_df)

    df_finale = pd.concat(records, ignore_index=True)
    return df_finale

@st.cache_data
def carica_riepilogo_originale():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name="Riepilogo Leo", index_col=0)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        return df
    except Exception as e:
        st.error(f"Errore durante il caricamento del riepilogo: {e}")
        st.stop()

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === FUNZIONE DI SALVATAGGIO ===
def salva_spese_formattato(df_spese):
    mesi = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
    ]

    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
        wb = writer.book
        if "Spese Leo" in wb.sheetnames:
            wb.remove(wb["Spese Leo"])
        ws = wb.create_sheet("Spese Leo", 0)

        header = []
        for mese in mesi:
            header.extend(["Testo", "Valore", "Tag"])
        ws.append(header)

        max_righe = 0
        for mese in mesi:
            mese_df = df_spese[df_spese["Mese"] == mese]
            max_righe = max(max_righe, len(mese_df))

        for i in range(max_righe):
            row = []
            for mese in mesi:
                mese_df = df_spese[df_spese["Mese"] == mese].reset_index(drop=True)
                if i < len(mese_df):
                    row.extend([
                        mese_df.loc[i, "Testo"],
                        mese_df.loc[i, "Valore"],
                        mese_df.loc[i, "Tag"]
                    ])
                else:
                    row.extend(["", "", ""])
            ws.append(row)

        writer.save()

# === INTERFACCIA ===

st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

# === VISTA 1: SPESE DETTAGLIATE ===
if vista == "Spese dettagliate":
    st.title("📌 Spese 2025")

    df_spese = carica_spese()

    mesi_disponibili = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
    ]
    mese_selezionato = st.selectbox("📅 Seleziona mese", mesi_disponibili)

    df_filtrato = df_spese[df_spese["Mese"] == mese_selezionato][["Testo", "Valore", "Tag"]].reset_index(drop=True)
    st.subheader(f"📝 Modifica spese di {mese_selezionato.capitalize()}")

    edited_df = st.data_editor(
        df_filtrato,
        column_config={
            "Testo": st.column_config.TextColumn("Descrizione"),
            "Valore": st.column_config.NumberColumn("Importo (€)"),
            "Tag": st.column_config.TextColumn("Categoria")
        },
        use_container_width=True,
        hide_index=True
    )

    df_spese.loc[df_spese["Mese"] == mese_selezionato, ["Testo", "Valore", "Tag"]] = edited_df

    st.subheader("➕ Aggiungi nuova spesa")
    with st.form(key="aggiungi_spesa"):
        nuovo_testo = st.text_input("Descrizione")
        nuovo_valore = st.number_input("Importo (€)", step=0.01)
        nuovo_tag = st.text_input("Categoria")
        submitted = st.form_submit_button("Aggiungi")

        if submitted and nuovo_testo and nuovo_valore != 0:
            nuova_riga = {
                "Testo": nuovo_testo,
                "Valore": nuovo_valore,
                "Tag": nuovo_tag,
                "Mese": mese_selezionato
            }
            df_spese = pd.concat([df_spese, pd.DataFrame([nuova_riga])], ignore_index=True)
            st.success("Spesa aggiunta!")

    if st.button("💾 Salva tutte le modifiche"):
        try:
            salva_spese_formattato(df_spese)
            st.cache_data.clear()
            st.success(f"File aggiornato correttamente!")
        except Exception as e:
            st.error(f"Errore nel salvataggio: {e}")

    buffer = io.BytesIO()
    df_spese.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button(
        label="⬇️ Scarica spese aggiornate",
        data=buffer,
        file_name="Spese_App_modificato.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# === VISTA 2: RIEPILOGO MENSILE ===
elif vista == "Riepilogo mensile":
    st.title("📊 Riepilogo mensile")

    df_spese = carica_spese()

    macrocategorie = {
        "Entrate": ["Stipendio", "Affitto Savoldo 4 + generico"],
        "Uscite necessarie": [
            "PAC Investimenti", "Donazioni (StC, Unicef, Greenpeace)", "Mutuo", "Luce&Gas",
            "Internet/Telefono", "Mezzi", "Spese condominiali", "Spese comuni",
            "Auto (benzina, noleggio, pedaggi, parcheggi)", "Spesa cibo", "Tari", "Unobravo"
        ],
        "Uscite variabili": [
            "Amazon", "Bolli governativi", "Farmacia/Visite", "Food Delivery", "Generiche", "Multa",
            "Uscite (Pranzi,Cena,Apericena,Pub,etc)", "Prelievi", "Regali", "Sharing (auto, motorino, bici)",
            "Shopping (vestiti, mobili,...)", "Stireria", "Viaggi (treno, aereo, hotel, attrazioni, concerti, cinema)"
        ]
    }

    df_spese["Mese"] = df_spese["Mese"].str.lower()
    df_spese["Tag"] = df_spese["Tag"].str.strip()

    df_riep = df_spese.groupby(["Tag", "Mese"])["Valore"].sum().unstack(fill_value=0)
    mesi_ordinati = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
    ]
    df_riep = df_riep[[m for m in mesi_ordinati if m in df_riep.columns]]

    righe_finali = []
    for categoria, tag_list in macrocategorie.items():
        intestazione = pd.Series([None] * len(df_riep.columns), index=df_riep.columns, name=categoria)
        righe_finali.append(intestazione)
        for tag in tag_list:
            if tag in df_riep.index:
                righe_finali.append(df_riep.loc[tag])

    df_riep_cat = pd.DataFrame(righe_finali)

    df_formattato = df_riep_cat.copy()
    for col in df_formattato.columns:
        df_formattato[col] = df_formattato[col].apply(
            lambda x: formatta_euro(x) if pd.notnull(x) and isinstance(x, (int, float)) else ""
        )

    st.dataframe(df_formattato, use_container_width=True, hide_index=False)

# === VISTA 3: DASHBOARD ===
elif vista == "Dashboard":
    st.title("📈 Dashboard")

    df_spese = carica_spese()

    macrocategorie = {
        "Entrate": ["Stipendio", "Affitto Savoldo 4 + generico"],
        "Uscite necessarie": [
            "PAC Investimenti", "Donazioni (StC, Unicef, Greenpeace)", "Mutuo", "Luce&Gas",
            "Internet/Telefono", "Mezzi", "Spese condominiali", "Spese comuni",
            "Auto (benzina, noleggio, pedaggi, parcheggi)", "Spesa cibo", "Tari", "Unobravo"
        ],
        "Uscite variabili": [
            "Amazon", "Bolli governativi", "Farmacia/Visite", "Food Delivery", "Generiche", "Multa",
            "Uscite (Pranzi,Cena,Apericena,Pub,etc)", "Prelievi", "Regali", "Sharing (auto, motorino, bici)",
            "Shopping (vestiti, mobili,...)", "Stireria", "Viaggi (treno, aereo, hotel, attrazioni, concerti, cinema)"
        ]
    }

    df_spese["Mese"] = df_spese["Mese"].str.lower()
    df_spese["Tag"] = df_spese["Tag"].str.strip()

    df_macrocategorie = pd.DataFrame()
    for categoria, tags in macrocategorie.items():
        df_categoria = df_spese[df_spese["Tag"].isin(tags)]
        df_grouped = df_categoria.groupby("Mese")["Valore"].sum()
        df_macrocategorie.loc[categoria] = df_grouped

    df_macrocategorie = df_macrocategorie.fillna(0)
    df_macrocategorie.loc["Risparmio mese"] = (
        df_macrocategorie.loc["Entrate"]
        - df_macrocategorie.loc["Uscite necessarie"]
        - df_macrocategorie.loc["Uscite variabili"]
    )
    df_macrocategorie.loc["Risparmio cumulato"] = df_macrocategorie.loc["Risparmio mese"].cumsum()

    from datetime import datetime
    mese_attuale = datetime.today().month
    mesi_ytd = df_macrocategorie.columns[:mese_attuale]
    df_macrocategorie["Media YTD"] = df_macrocategorie[mesi_ytd].mean(axis=1)

    df_tabella = df_macrocategorie.reset_index().rename(columns={"index": "Voce"})
    for col in df_tabella.columns[1:]:
        df_tabella[col] = df_tabella[col].apply(lambda x: formatta_euro(x) if pd.notnull(x) else "€ 0,00")

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_tabella, use_container_width=True, hide_index=True)

    df_grafico = df_macrocategorie.drop(columns=["Media YTD"], errors="ignore").transpose()
    st.subheader("📈 Andamento mensile")
    fig, ax = plt.subplots(figsize=(12, 6))
    df_grafico.plot(kind="bar", ax=ax)
    ax.set_title("Entrate, Uscite e Risparmio per mese")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Importo (€)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
