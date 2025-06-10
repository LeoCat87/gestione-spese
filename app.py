import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
 
st.set_page_config(page_title="Gestione Spese", layout="wide")
st.write("Streamlit version:", st.__version__)

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
    df = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
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
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df
 
@st.cache_data
def carica_dashboard():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df["Total"] = df.get("Total", pd.Series(0))  # Se manca "Total", metti 0
    return df

# --- Funzione per caricare i tag da "Riepilogo 2025" (prima colonna) ---
@st.cache_data
def carica_tag_da_riepilogo():
    df_riepilogo = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo 2025", index_col=0)
    # I tag sono gli indici (riga), quindi li prendiamo come lista
    return list(df_riepilogo.index)

# --- Funzione per salvare i dati modificati su Excel ---
def salva_spese_modificate(df):
    # Carica file Excel completo
    with pd.ExcelWriter(EXCEL_PATH, mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name="Spese 2025", index=False, header=True, startrow=1)
    st.success("Modifiche salvate con successo!")
 
def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
 
# === INTERFACCIA ===
 
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])
 
# === VISTA 1: SPESE DETTAGLIATE ===
 
if vista == "Spese dettagliate":
    st.title("📌 Spese Dettagliate")

    # Carica dati e tag
    df_spese = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=[1])
    df_spese = df_spese.loc[:, ~df_spese.columns.str.contains('^Unnamed')]

    tag_options = carica_tag_da_riepilogo()

    # Filtri base (opzionali)
    filtro_testo = st.text_input("Filtra per 'Testo'")
    filtro_tag = st.multiselect("Filtra per 'Tag'", options=tag_options, default=tag_options)

    df_filtrato = df_spese.copy()
    if filtro_testo:
        df_filtrato = df_filtrato[df_filtrato["Testo"].str.contains(filtro_testo, case=False, na=False)]
    if filtro_tag:
        df_filtrato = df_filtrato[df_filtrato["Tag"].isin(filtro_tag)]

    # Prepara opzioni per dropdown nella colonna 'Tag'
    # Streamlit 1.24+ permette opzioni di dropdown per st.data_editor via il parametro 'column_config'
    col_config = {
    "Tag": st.column_config.SelectboxColumn(
        "Tag",
        options=tag_options,
        help="Seleziona il Tag da elenco"
    )
}

edited_df = st.data_editor(
    df_filtrato,
    use_container_width=True,
    column_config=col_config,
    num_rows="dynamic"
)

    # Configurazione dropdown per colonna Tag
    # La sintassi aggiornata è tramite column_config (Streamlit 1.24+)
    # Usa st.data_editor con column_config

    from streamlit import data_editor
    # Definisco la configurazione per colonna Tag con dropdown
    col_config = {
        "Tag": st.column_config.SelectboxColumn(
            "Tag",
            options=tag_options,
            help="Seleziona il Tag da elenco"
        )
    }

    # Mostra tabella modificabile con filtro e dropdown su Tag
    edited_df = st.data_editor(
        df_filtrato,
        use_container_width=True,
        column_config=col_config,
        num_rows="dynamic"  # permette aggiungere o rimuovere righe
    )

    # Bottone per salvare le modifiche
    if st.button("💾 Salva modifiche"):
        try:
            salva_spese_modificate(edited_df)
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

    # Inizializza DataFrame
    mesi = df_riepilogo.columns
    df_macrocategorie = pd.DataFrame(columns=mesi)

    for macro, sottotag in mappa_macrocategorie.items():
        tag_presenti = [t for t in sottotag if t in df_riepilogo.index]
        somma = df_riepilogo.loc[tag_presenti].sum() if tag_presenti else pd.Series([0] * len(mesi), index=mesi)
        df_macrocategorie.loc[macro] = somma

    # Calcoli aggiuntivi
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
