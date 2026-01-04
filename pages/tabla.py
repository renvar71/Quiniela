import streamlit as st
import sqlite3
from db import DB

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
        u.nombre,
        SUM(p.puntos) AS total_puntos
    FROM puntajes p
    JOIN usuarios u ON u.email = p.usuario_id
    GROUP BY u.nombre
    ORDER BY total_puntos DESC
""")

ranking = cur.fetchall()
conn.close()

# -------------------------
# MOSTRAR TABLA
# -------------------------
if not ranking:
    st.info("Aún no hay puntajes calculados")
else:
    col1, col2 = st.columns([1, 1])

    col1.markdown("**Usuario**")
    col2.markdown("**Puntos**")

    st.divider()

    for nombre, puntos in ranking:
        c1, c2 = st.columns([1, 1])
        c1.write(nombre)
        c2.write(int(puntos))
