import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- KONFIGURACIJA ---
st.set_page_config(page_title="Moj Planer Pro", layout="centered")

conn = sqlite3.connect('opravila.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS naloge
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              ime TEXT, prioriteta INTEGER, rok TEXT, 
              opravljeno INTEGER, arhivirano INTEGER DEFAULT 0, kategorija TEXT)''')
conn.commit()

# --- POMOŽNE FUNKCIJE ---
def posodobi_status(id_naloge, status):
    c.execute("UPDATE naloge SET opravljeno=? WHERE id=?", (status, id_naloge))
    conn.commit()

def izbrisi_nalogo(id_naloge):
    c.execute("DELETE FROM naloge WHERE id=?", (id_naloge,))
    conn.commit()

# --- STRANSKI MENI (DODAJANJE) ---
with st.sidebar:
    st.header("➕ Nova naloga")
    novo_ime = st.text_input("Ime nalog")
    nova_kat = st.selectbox("Kategorija", ["Splošno", "Šola", "Delo", "Dom", "Hobi"])
    nova_prio = st.select_slider("Prioriteta", options=[1, 2, 3], 
                                 format_func=lambda x: ["Visoka", "Srednja", "Nizka"][x-1])
    nov_rok = st.date_input("Rok", datetime.now())
    
    if st.button("Shrani v seznam"):
        if novo_ime:
            c.execute("INSERT INTO naloge (ime, prioriteta, rok, opravljeno, arhivirano, kategorija) VALUES (?, ?, ?, 0, 0, ?)",
                      (novo_ime, nova_prio, nov_rok.strftime("%d.%m.%Y"), nova_kat))
            conn.commit()
            st.success("Dodano!")
            st.rerun()

# --- GLAVNI VMESNIK ---
st.title("📝 Moj Pametni Planer")

# Statistika v vrstici
c.execute("SELECT COUNT(*) FROM naloge WHERE arhivirano=0 AND opravljeno=0")
st.write(f"Aktivnih nalog: **{c.fetchone()[0]}**")

tab1, tab2, tab3 = st.tabs(["📋 Seznam", "🔍 Iskanje", "📦 Arhiv"])

with tab1:
    # Filtri za prikaz
    prikaz_kat = st.multiselect("Filtriraj kategorije", ["Splošno", "Šola", "Delo", "Dom", "Hobi"])
    
    query = "SELECT * FROM naloge WHERE arhivirano=0 AND opravljeno=0"
    if prikaz_kat:
        query += f" AND kategorija IN ({','.join(['?']*len(prikaz_kat))})"
        df = pd.read_sql_query(query, conn, params=prikaz_kat)
    else:
        df = pd.read_sql_query(query, conn)

    if not df.empty:
        for _, row in df.iterrows():
            with st.expander(f"{'🔴' if row['prioriteta']==1 else '🔵'} {row['ime']} | {row['kategorija']}"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"📅 Rok: {row['rok']}")
                if col2.button("✔️ Opravljeno", key=f"done_{row['id']}"):
                    posodobi_status(row['id'], 1)
                    st.rerun()
                if col3.button("🗑️ Izbriši", key=f"del_{row['id']}"):
                    izbrisi_nalogo(row['id'])
                    st.rerun()
    else:
        st.info("Seznam je prazen. Čas za kavo! ☕")

    if st.button("🚀 Arhiviraj opravljene"):
        c.execute("UPDATE naloge SET arhivirano=1 WHERE opravljeno=1")
        conn.commit()
        st.rerun()

with tab2:
    iskanje = st.text_input("Vpiši del imena...")
    if iskanje:
        res = pd.read_sql_query("SELECT * FROM naloge WHERE ime LIKE ?", conn, params=(f"%{iskanje}%",))
        st.dataframe(res, use_container_width=True)

with tab3:
    st.write("Zgodovina arhiviranih nalog:")
    arhiv_df = pd.read_sql_query("SELECT kategorija, ime, rok FROM naloge WHERE arhivirano=1 ORDER BY id DESC", conn)
    st.table(arhiv_df)
