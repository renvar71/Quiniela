import streamlit as st
from db import save_prediccion, DB
import pandas as pd
import random
import sqlite3

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

if "partido_id" not in st.session_state:
    st.switch_page("pages/menu_predicciones.py")

partido_id = st.session_state.partido_id
semana = st.session_state.semana
local = st.session_state.local
visitante = st.session_state.visitante
user_id = st.session_state.user_id

# cargar pregunta aleatoria (una sola vez)
if "pregunta_extra" not in st.session_state:
    df = pd.read_csv("preguntas.csv")
    preguntas = df["pregunta"].dropna().tolist()
    random.seed(partido_id)
    st.session_state.pregunta_extra = random.choice(preguntas)


pregunta = st.session_state.pregunta_extra
equipos = [local, visitante]

# --- CSS SOLO para el submit del form ---
st.markdown("""
<style>
div[data-testid="stForm"] button {
    background-color: #28a745;
    color: white;
}
div[data-testid="stForm"] button:hover {
    background-color: #218838;
}
</style>
""", unsafe_allow_html=True)

if st.button("⬅️"):
    st.switch_page("pages/menu_predicciones.py")

st.title("🎯 Registrar predicción")
st.subheader(f"Semana {semana}")
st.write(f"{local} vs {visitante}")

with st.form("form_prediccion"):

    ganador = st.radio("Selecciona ganador", [local, visitante], horizontal=True)
    score_local = st.number_input(f"Marcador {local}:", 0, 100, 0)
    score_away = st.number_input(f"Marcador {visitante}:", 0, 100, 0)
    line = st.radio("Over/Under total puntos", ["Over", "Under"], horizontal=True)
    st.markdown("Pregunta extra:")
    extra = st.radio(pregunta, [local, visitante], horizontal=True)
    submit = st.form_submit_button("Guardar Predicción")

    if submit:
        save_prediccion(
            user_id=user_id,
            partido_id=partido_id,
            semana=semana,
            pick=ganador,
            score_local=score_local,
            score_away=score_away,
            line_over_under=line,
            extra_question=extra
        )
        st.success("✅ Predicción guardada")
        st.switch_page("pages/menu_predicciones.py")
