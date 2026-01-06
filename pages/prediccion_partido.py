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
# VALIDAR CONTEXTO REAL
# -------------------------
required_keys = [
    "partido_id", "semana", "local",
    "visitante", "fecha_partido", "user_id"
]

if not all(st.session_state.get(k) is not None for k in required_keys):
    st.switch_page("pages/menu_predicciones.py")

partido_id = st.session_state.partido_id
semana = st.session_state.semana
local = st.session_state.local
visitante = st.session_state.visitante
fecha_partido = st.session_state.fecha_partido
user_id = st.session_state.user_id

# -------------------------
# PREGUNTAS EXTRA (2 por partido)
# -------------------------
if (
    "preguntas_extra" not in st.session_state
    or st.session_state.get("preguntas_partido_id") != partido_id
):
    df = pd.read_csv("preguntas.csv")
    preguntas = df["pregunta"].dropna().tolist()

    random.seed(partido_id)
    st.session_state.preguntas_extra = random.sample(preguntas, 2)
    st.session_state.preguntas_partido_id = partido_id

pregunta_1, pregunta_2 = st.session_state.preguntas_extra

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
    for k in [
        "partido_id", "semana", "local", "visitante",
        "fecha_partido", "preguntas_extra", "preguntas_partido_id"
    ]:
        st.session_state.pop(k, None)

    st.switch_page("pages/menu_predicciones.py")

# -------------------------
# UI
# -------------------------
st.title("🎯 Registrar predicción")
st.subheader(f"Semana {semana}")
st.write(f"**{local} vs {visitante}**")

# -------------------------
# FORM
# -------------------------
with st.form("form_prediccion"):

    # -------------------------
# MARCADOR VISUAL
# -------------------------
    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])
    
    with col1:
        st.image(
            f"logos/{local}.png",  # o URL
            use_container_width=True
        )
        st.markdown(f"<h4 style='text-align:center'>{local}</h4>", unsafe_allow_html=True)
    
    with col3:
        score_local = st.number_input(
            "",
            min_value=0,
            max_value=100,
            step=1,
            key="score_local"
        )
    
    with col4:
        st.markdown("<h2 style='text-align:center'>:</h2>", unsafe_allow_html=True)
    
    with col5:
        score_away = st.number_input(
            "",
            min_value=0,
            max_value=100,
            step=1,
            key="score_away"
        )
    
    with col2:
        st.image(
            f"logos/{visitante}.png",  # o URL
            use_container_width=True
        )
        st.markdown(f"<h4 style='text-align:center'>{visitante}</h4>", unsafe_allow_html=True)


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

    st.markdown("**Preguntas extra:**")

    extra_1 = st.radio(
        pregunta_1,
        [local, visitante],
        horizontal=True,
        key="extra_1"
    )

    extra_2 = st.radio(
        pregunta_2,
        [local, visitante],
        horizontal=True,
        key="extra_2"
    )

    submit = st.form_submit_button("Guardar Predicción")

# -------------------------
# CALCULAR EL GANADOR
# -------------------------

if score_local > score_away:
    ganador = local
elif score_away > score_local:
    ganador = visitante
else:
    ganador = "Empate"

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
        extra_question_1=extra_1,
        extra_question_2=extra_2
    )

    st.success("✅ Predicción guardada")

    for k in [
        "partido_id", "semana", "local", "visitante",
        "fecha_partido", "preguntas_extra", "preguntas_partido_id"
    ]:
        st.session_state.pop(k, None)

    st.switch_page("pages/menu_predicciones.py")
