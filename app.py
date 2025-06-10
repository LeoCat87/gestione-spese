import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
from datetime import datetime

st.set_page_config(page_title="Gestione Spese", layout="wide")

# === CONFIGURAZIONE ===
GDRIVE_FILE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
EXCEL_PATH = "Spese_Leo.xlsx"

# Scarica il file Excel da Google Drive
@st.cache_data
def scarica_excel_da_drive():
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    gdown.download(url, EXCEL_PATH, quiet=True)

scarica_excel_da_drive()

# === FUNZIONI DI CARICAMENTO ===
@st.cache_data
def carica_spese_grezze():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how="all")
    return df

@st.cache_data
def carica_riepilogo():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese 2025 (modificabile)", "Riepilogo mensile", "Dashboard"])

# === VISTA 1: MODIFICA FOGLIO SPESE ===
if vista == "Spese 2025 (modificabile)":
    st.title("📋 Modifica Spese 2025")
    df = carica_spese_grezze()

    # Rendi modificabile la colonna 'Tag' con dropdown
    riepilogo_df = carica_riepilogo()
    tag_options = sorted(riepilogo_df.index.unique())

    col_config = {
        "Tag": st.column_config.SelectboxColumn(
            "Tag",
            options=tag_options,
            help="Seleziona il Tag da elenco"
        )
    }

    modificato = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config=col_config,
        key="editor_spese",
        disabled=[]
    )

    if st.button("🔖 Salva modifiche nel file Excel"):
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            modificato.to_excel(writer, sheet_name="Spese 2025", index=False, startrow=1)
        st.success("Modifiche salvate con successo nel file Excel.")

# === VISTA 2: RIEPILOGO MENSILE ===
elif vista == "Riepilogo mensile":
    st.title("📊 Riepilogo Mensile per Tag")
    df_riepilogo = carica_riepilogo()
    df_formattato = df_riepilogo.applymap(lambda x: formatta_euro(x) if isinstance(x, (int, float)) else x)
    st.dataframe(df_formattato, use_container_width=True, hide_index=True)

# === VISTA 3: DASHBOARD ===
elif vista == "Dashboard":
    st.title("📈 Dashboard")
    df_riepilogo = carica_riepilogo()

    mappa_macrocategorie = {
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

    mesi = df_riepilogo.columns
    df_macrocategorie = pd.DataFrame(columns=mesi)

    for macro, sottotag in mappa_macrocategorie.items():
        tag_presenti = [t for t in sottotag if t in df_riepilogo.index]
        if tag_presenti:
            df_macrocategorie.loc[macro] = df_riepilogo.loc[tag_presenti].sum()
        else:
            df_macrocategorie.loc[macro] = pd.Series([0] * len(mesi), index=mesi)

    df_macrocategorie.loc["Risparmio mese"] = (
        df_macrocategorie.loc["Entrate"]
        - df_macrocategorie.loc["Uscite necessarie"]
        - df_macrocategorie.loc["Uscite variabili"]
    )

    df_macrocategorie.loc["Risparmio cumulato"] = df_macrocategorie.loc["Risparmio mese"].cumsum()

    # Calcola media fino al mese precedente
    mese_attuale = datetime.now().month
    if mese_attuale > 1:
        mesi_media = mesi[:mese_attuale - 1]
        media_valori = df_macrocategorie[mesi_media].mean(axis=1).rename("Media")
        df_macrocategorie["Media"] = media_valori

    df_tabella = df_macrocategorie.copy().reset_index().rename(columns={"index": "Voce"})
    for col in df_tabella.columns[1:]:
        df_tabella[col] = df_tabella[col].apply(lambda x: formatta_euro(x) if pd.notnull(x) else "€ 0,00")

    st.subheader("\ud83d\udcca Tabella riepilogo")
    st.dataframe(df_tabella, use_container_width=True, hide_index=True)

    df_grafico = df_macrocategorie.drop(columns="Media", errors="ignore").transpose()
    st.subheader("\ud83d\udcc8 Andamento mensile")
    fig, ax = plt.subplots(figsize=(12, 6))
    df_grafico.plot(kind="bar", ax=ax)
    ax.set_title("Entrate, Uscite e Risparmio per mese")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Importo (€)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
