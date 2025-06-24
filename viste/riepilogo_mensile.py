
import streamlit as st
import pandas as pd

def mostra_riepilogo_mensile(EXCEL_PATH, nome_foglio, formatta_euro):
    st.title("📊 Riepilogo Mensile per Tag")

    mappa_macrocategorie = {
        "📌 Entrate": ["Stipendio", "Affitto Savoldo 4 + generico"],
        "📌 Uscite necessarie": [
            "PAC Investimenti", "Donazioni (StC, Unicef, Greenpeace)", "Mutuo", "Luce&Gas",
            "Internet/Telefono", "Mezzi", "Spese condominiali", "Spese comuni",
            "Auto (benzina, noleggio, pedaggi, parcheggi)", "Spesa cibo", "Tari", "Unobravo"
        ],
        "📌 Uscite variabili": [
            "Amazon", "Bolli governativi", "Farmacia/Visite", "Food Delivery", "Generiche", "Multa",
            "Uscite (Pranzi,Cena,Apericena,Pub,etc)", "Prelievi", "Regali", "Sharing (auto, motorino, bici)",
            "Shopping (vestiti, mobili,...)", "Stireria", "Viaggi (treno, aereo, hotel, attrazioni, concerti, cinema)"
        ]
    }

    sheet = pd.read_excel(EXCEL_PATH, sheet_name=nome_foglio("Spese"), header=None)
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

        mese_corr = pd.Timestamp.today().month
        mesi_da_media = mesi_ordinati[:mese_corr - 1] if mese_corr > 1 else []
        if mesi_da_media:
            df_riepilogo["Media YTD"] = df_riepilogo[mesi_da_media].mean(axis=1)
        else:
            df_riepilogo["Media YTD"] = 0

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
        st.warning("Nessuna spesa trovata nei blocchi mensili del foglio.")
