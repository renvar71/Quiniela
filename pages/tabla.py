import streamlit as st
import sqlite3
from db import DB
import pandas as pd

# -------------------------
# SESSION CHECK
# -------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

st.title("📊 Tabla General")

# -------------------------
# OBTENER RANKING
# -------------------------
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
    SELECT 
        u.nombre AS Usuario,
        COALESCE(SUM(p.puntos), 0) AS Puntos
    FROM usuarios u
    LEFT JOIN puntajes p ON u.email = p.usuario_id
    GROUP BY u.nombre
    ORDER BY Puntos DESC
""")

ranking = cur.fetchall()
conn.close()

# -------------------------
# MOSTRAR TABLA
# -------------------------
df = pd.DataFrame(ranking, columns=["Usuario", "Puntos"])
st.table(df)
