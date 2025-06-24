
import streamlit as st
import openpyxl
import pandas as pd

def mostra_spese_dettagliate(EXCEL_PATH, anno, persona, nome_foglio, carica_spese, carica_riepilogo, formatta_euro):
    st.title("📌 Spese Dettagliate")
    df_spese = carica_spese(anno, persona)
    df_riepilogo = carica_riepilogo(anno, persona)

    mesi_disponibili = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

    mappa_macrocategorie = {
        "Entrate": ["Stipendio", "Entrate extra", "Affitto Savoldo 4 + generico"],
        "Uscite necessarie": [
            "Affitto", "Bollette", "Spesa", "Abbonamenti", "Trasporti", "Assicurazione",
            "PAC Investimenti", "Mutuo", "Luce&Gas", "Internet/Telefono", "Mezzi",
            "Spese condominiali", "Spese comuni", "Auto (benzina, noleggio, pedaggi, parcheggi)",
            "Spesa cibo", "Tari", "Unobravo", "Donazioni (StC, Unicef, Greenpeace)"
        ],
        "Uscite variabili": [
            "Amazon", "Bolli governativi", "Farmacia/Visite", "Food Delivery", "Generiche",
            "Multa", "Uscite (Pranzi,Cena,Apericena,Pub,etc)", "Prelievi", "Regali",
            "Sharing (auto, motorino, bici)", "Shopping (vestiti, mobili,...)", "Stireria",
            "Viaggi (treno, aereo, hotel, attrazioni, concerti, cinema)"
        ]
    }

    col1, col2 = st.columns([1, 5])
    with col2:
        st.markdown("### ➕ Inserisci una nuova spesa")

        nuovo_testo = st.text_input("Descrizione", "")
        nuovo_valore = st.number_input("Importo (€)", step=0.01, format="%.2f")
        nuova_categoria = st.selectbox("Macrocategoria", list(mappa_macrocategorie.keys()))
        nuovo_tag = st.selectbox("Tag", mappa_macrocategorie[nuova_categoria])
        nuovo_mese = st.selectbox("Mese", mesi_disponibili)

        if st.button("➕ Aggiungi spesa"):
            if nuovo_testo.strip() == "" or nuovo_valore == 0:
                st.warning("⚠️ Inserisci una descrizione e un valore diverso da zero.")
            else:
                wb = openpyxl.load_workbook(EXCEL_PATH)
                ws = wb[nome_foglio("Spese")]

                mesi_excel = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                              "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
                mese_col_start = None
                for col in range(1, ws.max_column + 1):
                    val = ws.cell(row=1, column=col).value
                    if val and isinstance(val, str) and val.lower() == nuovo_mese.lower():
                        mese_col_start = col
                        break

                if mese_col_start:
                    row_idx = 3
                    while ws.cell(row=row_idx, column=mese_col_start).value not in [None, ""]:
                        row_idx += 1

                    ws.cell(row=row_idx, column=mese_col_start).value = nuovo_testo
                    ws.cell(row=row_idx, column=mese_col_start + 1).value = float(nuovo_valore)
                    ws.cell(row=row_idx, column=mese_col_start + 2).value = nuovo_tag

                    wb.save(EXCEL_PATH)
                    st.success("✅ Spesa aggiunta correttamente.")
                    st.experimental_rerun()
                else:
                    st.error("❌ Colonna del mese non trovata nel foglio Excel.")
