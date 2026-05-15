import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Nastavitve strani
st.set_page_config(page_title="Moj Planer", layout="centered")

# Povezava z bazo
conn = sqlite3.connect('opravila.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS naloge
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              ime TEXT, prioriteta INTEGER, rok TEXT, 
              opravljeno INTEGER, arhivirano INTEGER DEFAULT 0, kategorija TEXT)''')
conn.commit()

st.title("📝 Moj Mobilni Planer")

# --- DODAJANJE (V RAZŠIRLJIVEM MENIJU) ---
with st.expander("➕ Dodaj novo nalogo"):
    novo_ime = st.text_input("Ime naloge")
    nova_kat = st.selectbox("Kategorija", ["Splošno", "Šola", "Delo", "Dom", "Hobi"])
    nova_prio = st.select_slider("Prioriteta", options=[1, 2, 3], format_func=lambda x: ["Visoka", "Srednja", "Nizka"][x-1])
    nov_rok = st.date_input("Rok", datetime.now())
    
    if st.button("Shrani nalogo"):
        if novo_ime:
            c.execute("INSERT INTO naloge (ime, prioriteta, rok, opravljeno, arhivirano, kategorija) VALUES (?, ?, ?, 0, 0, ?)",
                      (novo_ime, nova_prio, nov_rok.strftime("%d.%m.%Y"), nova_kat))
            conn.commit()
            st.success("Dodano!")
            st.rerun()

# --- PRIKAZ IN UPRAVLJANJE ---
tab1, tab2 = st.tabs(["📋 Aktivno", "📦 Arhiv"])

with tab1:
    # Pridobimo podatke
    df = pd.read_sql_query("SELECT id, kategorija, ime, prioriteta, rok FROM naloge WHERE arhivirano=0 AND opravljeno=0", conn)
    
    if not df.empty:
        for index, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([0.8, 0.2])
                prio_oznaka = "🔴" if row['prioriteta'] == 1 else ("🟡" if row['prioriteta'] == 2 else "🔵")
                col1.write(f"{prio_oznaka} **{row['ime']}** ({row['kategorija']})")
                col1.caption(f"Rok: {row['rok']}")
                if col2.button("✔️", key=f"btn_{row['id']}"):
                    c.execute("UPDATE naloge SET opravljeno=1 WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()
                st.divider()
    else:
        st.info("Ni aktivnih nalog.")

    if st.button("🚀 Arhiviraj opravljene"):
        c.execute("UPDATE naloge SET arhivirano=1 WHERE opravljeno=1")
        conn.commit()
        st.rerun()

with tab2:
    arhiv_df = pd.read_sql_query("SELECT kategorija, ime, rok FROM naloge WHERE arhivirano=1", conn)
    st.dataframe(arhiv_df, use_container_width=True, hide_index=True)
