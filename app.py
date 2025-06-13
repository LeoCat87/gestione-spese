import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gdown
st.set_page_config(page_title="Gestione Spese", layout="wide")
# === CONFIGURAZIONE ===
GDRIVE_FILE_ID = "1PJ9TCcq4iBHeg8CpC1KWss0UWSg86BJn"
EXCEL_PATH = "Spese_App.xlsx"
# Scarica il file Excel da Google Drive
@st.cache_data
def scarica_excel_da_drive():
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    gdown.download(url, EXCEL_PATH, quiet=True)
scarica_excel_da_drive()
# === FUNZIONI DI CARICAMENTO ===
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
@st.cache_data
def carica_dashboard():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Riepilogo Leo", index_col=0)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df["Total"] = df.get("Total", pd.Series(0))  # Se manca "Total", metti 0
    return df
def formatta_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
# === INTERFACCIA ===
st.sidebar.title("📁 Navigazione")
vista = st.sidebar.radio("Scegli una vista:", ["Spese dettagliate", "Riepilogo mensile", "Dashboard"])
# === VISTA 1: SPESE DETTAGLIATE ===
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

# === VISTA 2: RIEPILOGO MENSILE ===
elif vista == "Riepilogo mensile":
    st.title("📊 Riepilogo Mensile per Tag")

    mappa_macrocategorie = {
        "📌 Entrate": [...],
        "📌 Uscite necessarie": [...],
        "📌 Uscite variabili": [...]
    }

    sheet = pd.read_excel(EXCEL_PATH, sheet_name="Spese Leo", header=None)
    mesi_excel = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                  "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

    col_mese = {}
    for col_idx in range(sheet.shape[1]):
        cella = sheet.iloc[0, col_idx]
        if isinstance(cella, str) and cella.lower() in mesi_excel:
            col_mese[cella.lower()] = col_idx

    spese_totali = []
    for mese_lower, start_col in col_mese.items():
        intestazioni = sheet.iloc[1, start_col:start_col+3].tolist()
        if "Valore" in intestazioni and "Tag" in intestazioni:
            df_blocco = sheet.iloc[2:, start_col:start_col+3].copy()
            df_blocco.columns = intestazioni
            df_blocco = df_blocco.dropna(subset=["Valore", "Tag"])
            df_blocco["Mese"] = mese_lower.capitalize()
            spese_totali.append(df_blocco)

    if spese_totali:
        df_spese = pd.concat(spese_totali, ignore_index=True)
        df_riepilogo = df_spese.groupby(["Tag", "Mese"])["Valore"].sum().unstack(fill_value=0)

        mesi_ordinati = [m.capitalize() for m in mesi_excel]
        df_riepilogo = df_riepilogo.reindex(columns=mesi_ordinati, fill_value=0)

        from datetime import datetime
        mese_corr = datetime.today().month
        mesi_da_media = mesi_ordinati[:mese_corr - 1] if mese_corr > 1 else []
        if mesi_da_media:
            df_riepilogo["Media YTD"] = df_riepilogo[mesi_da_media].mean(axis=1)
        else:
            df_riepilogo["Media YTD"] = 0

        # Esporta
        df_export = df_riepilogo.reset_index().rename(columns={"index": "Categoria"})
        esporta_excel(df_export, nome_file="Riepilogo_mensile.xlsx")

        # HTML tabella
        html = """
        <style>
        table {border-collapse: collapse; width: auto; table-layout: auto;}
        th, td {padding: 6px 12px; text-align: left; white-space: nowrap;}
        .macro {background-color: #f0f0f0; font-weight: bold;}
        </style>
        <table>
            <tr>
                <th>Categoria</th>""" + "".join(f"<th>{mese}</th>" for mese in mesi_ordinati) + "<th>Media YTD</th></tr>"

        for macro, tags in mappa_macrocategorie.items():
            html += f'<tr class="macro"><td colspan="{len(mesi_ordinati)+2}">{macro}</td></tr>'
            for tag in tags:
                if tag in df_riepilogo.index:
                    r = df_riepilogo.loc[tag]
                    html += f"<tr><td>{tag}</td>"
                    for mese in mesi_ordinati:
                        euro = formatta_euro(r[mese]) if r[mese] else "€ 0,00"
                        html += f"<td>{euro}</td>"
                    media = formatta_euro(r["Media YTD"]) if r["Media YTD"] else "€ 0,00"
                    html += f"<td>{media}</td></tr>"

        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("Nessuna spesa trovata nei blocchi mensili del foglio 'Spese Leo'.")

# === VISTA 3: DASHBOARD ===
elif vista == "Dashboard":
    st.title("📈 Dashboard")

    # Mappatura manuale tag → macrocategorie
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

    # Carica dati spese e calcola riepilogo mensile da "Spese Leo"
    sheet = pd.read_excel(EXCEL_PATH, sheet_name="Spese Leo", header=None)
    mesi_excel = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                  "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

    col_mese = {}
    for col_idx in range(sheet.shape[1]):
        cella = sheet.iloc[0, col_idx]
        if isinstance(cella, str) and cella.lower() in mesi_excel:
            col_mese[cella.lower()] = col_idx

    spese_totali = []
    for mese_lower, start_col in col_mese.items():
        intestazioni = sheet.iloc[1, start_col:start_col+3].tolist()
        if "Valore" in intestazioni and "Tag" in intestazioni:
            df_blocco = sheet.iloc[2:, start_col:start_col+3].copy()
            df_blocco.columns = intestazioni
            df_blocco = df_blocco.dropna(subset=["Valore", "Tag"])
            df_blocco["Mese"] = mese_lower.capitalize()
            spese_totali.append(df_blocco)

    if not spese_totali:
        st.warning("Nessuna spesa trovata nel foglio 'Spese Leo'.")
    else:
        df_spese = pd.concat(spese_totali, ignore_index=True)
        df_riepilogo = df_spese.groupby(["Tag", "Mese"])["Valore"].sum().unstack(fill_value=0)

        mesi_ordinati = [m.capitalize() for m in mesi_excel]
        df_riepilogo = df_riepilogo.reindex(columns=mesi_ordinati, fill_value=0)

        # Calcolo macrocategorie
        df_macrocategorie = pd.DataFrame(columns=mesi_ordinati)
        for macro, sottotag in mappa_macrocategorie.items():
            tag_presenti = [t for t in sottotag if t in df_riepilogo.index]
            somma = df_riepilogo.loc[tag_presenti].sum() if tag_presenti else pd.Series([0]*len(mesi_ordinati), index=mesi_ordinati)
            df_macrocategorie.loc[macro] = somma

        # Risparmio mese & cumulato
        df_macrocategorie.loc["Risparmio mese"] = (
            df_macrocategorie.loc["Entrate"]
            - df_macrocategorie.loc["Uscite necessarie"]
            - df_macrocategorie.loc["Uscite variabili"]
        )
        df_macrocategorie.loc["Risparmio cumulato"] = df_macrocategorie.loc["Risparmio mese"].cumsum()

        # Media YTD fino al mese precedente
        from datetime import datetime
        mese_corr = datetime.today().month
        mesi_ytd = mesi_ordinati[:mese_corr - 1] if mese_corr > 1 else []
        df_macrocategorie["Media YTD"] = df_macrocategorie[mesi_ytd].mean(axis=1) if mesi_ytd else 0

        # Tabella formattata
        df_tabella = df_macrocategorie.copy().reset_index().rename(columns={"index": "Voce"})
        for col in df_tabella.columns[1:]:
            df_tabella[col] = df_tabella[col].apply(lambda x: formatta_euro(x) if pd.notnull(x) else "€ 0,00")

        st.subheader("📊 Tabella riepilogo")
        st.dataframe(df_tabella, hide_index=True)
        esporta_excel(df_tabella, nome_file="Dashboard_finanziaria.xlsx")

        # Grafico
        df_grafico = df_macrocategorie[mesi_ordinati].transpose()
        st.subheader("📈 Andamento mensile")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(12, 6))
        df_grafico.plot(kind='bar', ax=ax)
        ax.set_title("Entrate, Uscite e Risparmio per mese")
        ax.set_xlabel("Mese")
        ax.set_ylabel("Importo (€)")
        plt.xticks(rotation=45)
        st.pyplot(fig)
