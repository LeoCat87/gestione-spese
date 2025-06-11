import streamlit as st
import pandas as pd
import gdown
import openpyxl
import matplotlib.pyplot as plt

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
def carica_spese():
    # Carica il foglio 'Spese 2025' dal file Excel
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=1)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Rimuove le colonne non nominate
    df = df.reset_index(drop=True)
    # Assicuriamoci che 'Valore' sia numerico e 'Tag' sia stringa
    df["Valore"] = pd.to_numeric(df["Valore"], errors="coerce")
    df["Tag"] = df["Tag"].astype(str)
    df["Testo"] = df["Testo"].astype(str)  # Assicuriamoci che 'Testo' sia stringa
    return df

@st.cache_data
def carica_riepilogo():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

@st.cache_data
def carica_dashboard():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df["Total"] = df.get("Total", pd.Series(0))  # Se manca "Total", metti 0
    return df

def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# === INTERFACCIA ===

st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])

# === VISTA 1: SPESE 2025 ===
# === VISTA 1: SPESE 2025 ===
if vista == "Spese dettagliate":
    st.title("📌 Spese 2025")

    # Carica i dati delle spese
    df_spese = carica_spese()

    # Carica i tag disponibili dal foglio 'Riepilogo 2025'
    df_riepilogo = carica_riepilogo()
    tag_options = df_riepilogo.index.tolist()

    st.subheader("📝 Modifica le spese")

    # Tabella modificabile
    edited_df = st.data_editor(
        df_spese,
        column_config={
            "Testo": st.column_config.TextColumn("Descrizione"),
            "Valore": st.column_config.NumberColumn("Importo (€)", format="€ {value:,.2f}"),
            "Tag": st.column_config.SelectboxColumn("Categoria", options=tag_options)
        },
        use_container_width=True
    )

    # Bottone di salvataggio
    if st.button("💾 Salva le modifiche"):
        try:
            with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                edited_df.to_excel(writer, sheet_name="Spese 2025", index=False)
            st.success("Modifiche salvate con successo!")
        except Exception as e:
            st.error(f"Errore nel salvataggio: {e}")

# === VISTA 2: RIEPILOGO MENSILE ===
elif vista == "Riepilogo mensile":
    st.title("📊 Riepilogo Mensile per Tag")

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

    righe_finali = []

    for categoria, tag_list in mappa_macrocategorie.items():
        intestazione = pd.Series([None] * len(df_riepilogo.columns), index=df_riepilogo.columns, name=categoria)
        righe_finali.append(intestazione)

        for tag in tag_list:
            if tag in df_riepilogo.index:
                riga = df_riepilogo.loc[tag]
                riga.name = tag
                righe_finali.append(riga)

    df_riepilogo_cat = pd.DataFrame(righe_finali)

    # Formatta i valori in euro, lascia vuoto le righe intestazione
    df_formattato = df_riepilogo_cat.copy()
    for col in df_formattato.columns:
        df_formattato[col] = df_formattato[col].apply(
            lambda x: formatta_euro(x) if pd.notnull(x) and isinstance(x, (int, float)) else ""
        )

    st.dataframe(df_formattato, use_container_width=True, hide_index=False)

# === VISTA 3: DASHBOARD ===
elif vista == "Dashboard":
    st.title("📈 Dashboard")

    df_riepilogo = carica_riepilogo()

    # === Mappa tag a macrocategorie ===
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

    # Inizializza DataFrame per aggregare i dati
    mesi = df_riepilogo.columns
    df_macrocategorie = pd.DataFrame(columns=mesi)

    for macro, sottotag in mappa_macrocategorie.items():
        tag_presenti = [t for t in sottotag if t in df_riepilogo.index]
        if tag_presenti:
            somma = df_riepilogo.loc[tag_presenti].sum() if tag_presenti else pd.Series([0] * len(mesi), index=mesi)
            df_macrocategorie.loc[macro] = somma
        else:
            df_macrocategorie.loc[macro] = [0] * len(mesi)

    # Calcoli aggiuntivi: Risparmio mese e Risparmio cumulato
    df_macrocategorie.loc["Risparmio mese"] = (
        df_macrocategorie.loc["Entrate"]
        - df_macrocategorie.loc["Uscite necessarie"]
        - df_macrocategorie.loc["Uscite variabili"]
    )
    df_macrocategorie.loc["Risparmio cumulato"] = df_macrocategorie.loc["Risparmio mese"].cumsum()

    # === Media YTD ===
    from datetime import datetime
    mese_attuale = datetime.today().month
    mesi_ytd = mesi[:mese_attuale - 1]  # fino al mese precedente

    medie_ytd = df_macrocategorie[mesi_ytd].mean(axis=1)
    df_macrocategorie["Media YTD"] = medie_ytd

    # === Tabella formattata ===
    df_tabella = df_macrocategorie.reset_index().rename(columns={"index": "Voce"})
    for col in df_tabella.columns[1:]:
        df_tabella[col] = df_tabella[col].apply(lambda x: formatta_euro(x) if pd.notnull(x) else "€ 0,00")

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_tabella, use_container_width=True, hide_index=True)

    # === Grafico ===
    df_grafico = df_macrocategorie[mesi].transpose()
    st.subheader("📈 Andamento mensile")
    fig, ax = plt.subplots(figsize=(12, 6))
    df_grafico.plot(kind="bar", ax=ax)
    ax.set_title("Entrate, Uscite e Risparmio per mese")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Importo (€)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
