import streamlit as st
import sqlite3
from db import DB, get_prediccion_status

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

def get_user_id(email):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row[0]

user_id = get_user_id(st.session_state.user)
st.session_state.user_id = user_id

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""
SELECT p.partido_id, p.semana, p.fecha, e1.nombre, e2.nombre
FROM partidos p
JOIN equipos e1 ON p.equipo_local_id = e1.team_id
JOIN equipos e2 ON p.equipo_visitante_id = e2.team_id
ORDER BY p.fecha
""")
partidos = cur.fetchall()
conn.close()

st.title("📋 Partidos pendientes")
st.markdown("*Selecciona un partido para registrar tu predicción*")

pendientes = [
    p for p in partidos
    if get_prediccion_status(user_id, p[0], p[2]) == "🟡 Pendiente"
]

if not pendientes:
    st.success("🎉 No tienes partidos pendientes")
else:
    for partido_id, semana, _, local, visitante in pendientes:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"{local} vs {visitante}",
                key=partido_id,
                use_container_width=True
            ):
                st.session_state.partido_id = partido_id
                st.session_state.semana = semana
                st.session_state.local = local
                st.session_state.visitante = visitante
                st.switch_page("pages/prediccion_partido.py")
