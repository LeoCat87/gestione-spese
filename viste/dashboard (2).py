
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def mostra_dashboard(carica_riepilogo, formatta_euro, datetime):
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

    mesi = df_riepilogo.columns.tolist()
    df_macrocategorie = pd.DataFrame(columns=mesi)

    for macro, sottotag in mappa_macrocategorie.items():
        tag_presenti = [t for t in sottotag if t in df_riepilogo.index]
        somma = df_riepilogo.loc[tag_presenti].sum() if tag_presenti else pd.Series([0]*len(mesi), index=mesi)
        df_macrocategorie.loc[macro] = somma

    df_macrocategorie.loc["Risparmio mese"] = (
        df_macrocategorie.loc["Entrate"]
        - df_macrocategorie.loc["Uscite necessarie"]
        - df_macrocategorie.loc["Uscite variabili"]
    )
    df_macrocategorie.loc["Risparmio cumulato"] = df_macrocategorie.loc["Risparmio mese"].cumsum()

    mese_corr = datetime.today().month
    mesi_ytd = mesi[:mese_corr - 1] if mese_corr > 1 else []
    df_macrocategorie["Media YTD"] = df_macrocategorie[mesi_ytd].mean(axis=1) if mesi_ytd else 0

    df_tabella = df_macrocategorie.copy().reset_index().rename(columns={"index": "Voce"})
    for col in df_tabella.columns[1:]:
        df_tabella[col] = df_tabella[col].apply(lambda x: formatta_euro(x) if pd.notnull(x) else "€ 0,00")

    st.subheader("📊 Tabella riepilogo")
    st.dataframe(df_tabella, hide_index=True)

    df_grafico = df_macrocategorie[mesi].transpose()
    st.subheader("📈 Andamento mensile")
    fig, ax = plt.subplots(figsize=(12, 6))
    df_grafico.plot(kind='bar', ax=ax)
    ax.set_title("Entrate, Uscite e Risparmio per mese")
    ax.set_xlabel("Mese")
    ax.set_ylabel("Importo (€)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
