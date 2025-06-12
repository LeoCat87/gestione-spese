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
    df_raw = pd.read_excel(EXCEL_PATH, sheet_name="Spese 2025", header=1)
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
            sotto_df["Mese"] = mese
            sotto_df["Tag"] = sotto_df["Tag"].fillna('').astype(str).str.strip().str.capitalize()
            sotto_df["Testo"] = sotto_df["Testo"].fillna('').astype(str).str.strip()
            sotto_df["Valore"] = pd.to_numeric(sotto_df["Valore"], errors="coerce")
            records.append(sotto_df)

    df_finale = pd.concat(records, ignore_index=True)
    return df_finale


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
if vista == "Spese dettagliate":
    st.title("📌 Spese 2025")

    df_spese = carica_spese()
    df_riepilogo = carica_riepilogo()

    macrocategorie = ["Entrate", "Uscite necessarie", "Uscite variabili"]
    tag_options = [tag for tag in df_riepilogo.index.tolist() if tag not in macrocategorie]

    df_spese["Tag"] = df_spese["Tag"].str.strip()
    df_spese["Mese"] = df_spese["Mese"].str.strip()
    df_spese["Tag"] = df_spese["Tag"].fillna("")

    mesi_disponibili = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    mese_selezionato = st.selectbox("📅 Seleziona mese", mesi_disponibili)

    # === Mostra tabella filtrata ===
    df_filtrato = df_spese[df_spese["Mese"] == mese_selezionato][["Testo", "Valore", "Tag"]].reset_index(drop=True)
    st.subheader(f"📝 Modifica spese di {mese_selezionato}")
    edited_df = st.data_editor(
        df_filtrato,
        column_config={
            "Testo": st.column_config.TextColumn("Descrizione"),
            "Valore": st.column_config.NumberColumn("Importo (€)"),
            "Tag": st.column_config.SelectboxColumn("Categoria", options=tag_options + [""])
        },
        use_container_width=True,
        hide_index=True
    )

    df_spese.loc[df_spese["Mese"] == mese_selezionato, ["Testo", "Valore", "Tag"]] = edited_df

    st.subheader("➕ Aggiungi nuova spesa")
    with st.form(key="aggiungi_spesa"):
        nuovo_testo = st.text_input("Descrizione")
        nuovo_valore = st.number_input("Importo (€)", step=0.01)
        nuovo_tag = st.selectbox("Categoria", options=tag_options)
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

    st.subheader("📎 Carica spese da file")
    file_caricato = st.file_uploader("Carica un file Excel (.xlsx) o PDF", type=["xlsx", "pdf"])

    def estrai_testo_ocr_space(file_pdf, api_key="K84283602188957"):
        import requests
        st.info("📤 Invio del PDF al servizio OCR.Space...")
        files = {
            'file': (file_pdf.name, file_pdf, 'application/pdf')
        }
        data = {
            'apikey': api_key,
            'language': 'ita',
            'isOverlayRequired': False
        }
        response = requests.post('https://api.ocr.space/parse/image',
                                 files=files,
                                 data=data)
        result = response.json()

        if result.get("IsErroredOnProcessing"):
            raise ValueError("Errore OCR: " + result.get("ErrorMessage", ["Unknown"])[0])

        testo = ""
        for parsed in result["ParsedResults"]:
            testo += parsed["ParsedText"] + "\n"
        return testo

    if file_caricato is not None:
        import pandas as pd

        if file_caricato.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            try:
                df_upload = pd.read_excel(file_caricato)
                colonne_attese = ["Testo", "Valore", "Tag"]
                if all(col in df_upload.columns for col in colonne_attese):
                    df_upload = df_upload[colonne_attese]
                    df_upload["Mese"] = mese_selezionato
                    df_spese = pd.concat([df_spese, df_upload], ignore_index=True)
                    st.success(f"{len(df_upload)} spese caricate dal file Excel.")
                else:
                    st.error("Il file Excel deve contenere le colonne: Testo, Valore, Tag")
            except Exception as e:
                st.error(f"Errore nella lettura del file Excel: {e}")

        elif file_caricato.type == "application/pdf":
            try:
                import re
                from datetime import datetime

                testo_completo = estrai_testo_ocr_space(file_caricato)
                st.subheader("🧾 Testo OCR estratto dal PDF:")
                st.text(testo_completo[:3000])

                righe = testo_completo.splitlines()
                movimenti = []
                data_corrente = None
                descrizione = ""

                pattern_data = re.compile(r"\d{1,2} [a-zà]+ 2025", re.IGNORECASE)
                pattern_importo = re.compile(r"[-−–]?\d{1,3}(?:[\.,]\d{2})$")

                for riga in righe:
                    riga = riga.strip()
                    if pattern_data.match(riga.lower()):
                        data_corrente = riga.strip()
                        descrizione = ""
                        continue

                    if pattern_importo.search(riga) and data_corrente:
                        try:
                            valore_str = pattern_importo.search(riga).group()
                            valore = float(valore_str.replace(",", ".").replace("−", "-").replace("–", "-"))

                            data = datetime.strptime(data_corrente, "%d %B %Y")
                            mese = data.strftime("%B").capitalize()

                            testo_descrizione = descrizione.strip() or "Senza descrizione"
                            movimenti.append({
                                "Testo": testo_descrizione,
                                "Valore": valore,
                                "Tag": "",
                                "Mese": mese
                            })

                            data_corrente = None
                            descrizione = ""
                        except Exception:
                            continue
                    elif data_corrente:
                        descrizione += " " + riga

                if movimenti:
                    df_upload = pd.DataFrame(movimenti)
                    df_spese = pd.concat([df_spese, df_upload], ignore_index=True)
                    st.success(f"{len(df_upload)} spese importate dal PDF tramite OCR.")
                else:
                    st.warning("Nessuna spesa trovata tramite OCR.")

            except Exception as e:
                st.error(f"Errore durante l'OCR del PDF: {e}")

    if st.button("💾 Salva tutte le modifiche"):
        try:
            blocchi = []
            max_righe = 0

            for mese in mesi_disponibili:
                mese_df = df_spese[df_spese["Mese"] == mese][["Testo", "Valore", "Tag"]].reset_index(drop=True)
                max_righe = max(max_righe, len(mese_df))
                blocchi.append(mese_df)

            for i in range(len(blocchi)):
                righe_mancanti = max_righe - len(blocchi[i])
                if righe_mancanti > 0:
                    blocchi[i] = pd.concat([
                        blocchi[i],
                        pd.DataFrame([["", None, ""]] * righe_mancanti, columns=["Testo", "Valore", "Tag"])
                    ])

            df_ricostruito = pd.concat(blocchi, axis=1)

            with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                df_ricostruito.to_excel(writer, sheet_name="Spese 2025", index=False)

            st.success("Tutte le modifiche sono state salvate!")
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
