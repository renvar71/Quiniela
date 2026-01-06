import streamlit as st
import pandas as pd
import random
from datetime import datetime

from db import save_prediccion

# -------------------------
# SESSION CHECK
# -------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

# -------------------------
# VALIDAR CONTEXTO
# -------------------------
required_keys = ["partido_id", "semana", "local", "visitante", "fecha_partido"]

if not all(k in st.session_state for k in required_keys):
    st.switch_page("pages/menu_predicciones.py")

partido_id = st.session_state.partido_id
semana = st.session_state.semana
local = st.session_state.local
visitante = st.session_state.visitante
fecha_partido = st.session_state.fecha_partido
user_id = st.session_state.user_id

# -------------------------
# PREGUNTA EXTRA (1 sola vez por partido)
# -------------------------
if "pregunta_extra" not in st.session_state:
    df = pd.read_csv("preguntas.csv")
    preguntas = df["pregunta"].dropna().tolist()

    random.seed(partido_id)
    st.session_state.pregunta_extra = random.choice(preguntas)

pregunta = st.session_state.pregunta_extra

# -------------------------
# CSS BOTÓN FORM
# -------------------------
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

# -------------------------
# NAV BACK
# -------------------------
if st.button("⬅️ Volver"):
    st.switch_page("pages/menu_predicciones.py")

st.title("🎯 Registrar predicción")
st.subheader(f"Semana {semana}")
st.write(f"**{local} vs {visitante}**")

# -------------------------
# FORM
# -------------------------
with st.form("form_prediccion"):

    ganador = st.radio(
        "Selecciona ganador",
        [local, visitante],
        horizontal=True
    )

    score_local = st.number_input(
        f"Marcador {local}",
        min_value=0,
        max_value=100,
        step=1
    )

    score_away = st.number_input(
        f"Marcador {visitante}",
        min_value=0,
        max_value=100,
        step=1
    )

    line = st.radio(
        "Over / Under total puntos",
        ["Over", "Under"],
        horizontal=True
    )

    st.markdown("**Pregunta extra:**")
    extra = st.radio(
        pregunta,
        [local, visitante],
        horizontal=True
    )

    submit = st.form_submit_button("Guardar Predicción")

# -------------------------
# SUBMIT
# -------------------------
if submit:
    save_prediccion(
        usuario_id=user_id,
        partido_id=partido_id,
        semana=semana,
        fecha_partido=fecha_partido,
        pick=ganador,
        score_local=score_local,
        score_away=score_away,
        line_over_under=line,
        extra_question=extra
    )

    st.success("✅ Predicción guardada")
    st.switch_page("pages/menu_predicciones.py")
