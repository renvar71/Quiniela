# prediccion_partido.py
import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os
from api import get_team_badges
from db import save_prediccion

# -------------------------
# SESSION CHECK
# -------------------------
if not st.session_state.get("logged_in"):
    st.warning("Debes iniciar sesión")
    st.stop()

user_id = st.session_state.get("user_id")
if not user_id:
    st.switch_page("pages/menu_predicciones.py")
    st.stop()

# -------------------------
# VALIDAR CONTEXTO REAL
# -------------------------
required_keys = [
    "partido_id", "semana", "local",
    "visitante", "fecha_partido"
]

if not all(st.session_state.get(k) is not None for k in required_keys):
    for k in required_keys:
        st.session_state.pop(k, None)
    st.switch_page("pages/menu_predicciones.py")
    st.stop()

partido_id = st.session_state.partido_id
semana = st.session_state.semana
local = st.session_state.local
visitante = st.session_state.visitante
fecha_partido = st.session_state.fecha_partido

team_badges = get_team_badges()
# -------------------------
# PREGUNTAS EXTRA
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
# NAV BACK
# -------------------------
if st.button("⬅️ Volver"):
    for k in [
        "partido_id", "semana", "local", "visitante",
        "fecha_partido", "preguntas_extra",
        "preguntas_partido_id", "score_local",
        "score_away", "extra_1", "extra_2"
    ]:
        st.session_state.pop(k, None)

    st.switch_page("pages/menu_predicciones.py")
    st.stop()

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

    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])

    # LOGO LOCAL
    with col1:
        home_badge_url = st.session_state.get("home_badge_url") or ""
        if home_badge_url:
            st.markdown(
                f'<div style="text-align:center">'
                f'<img src="{home_badge_url}" width="80">'
                f'</div>',
                unsafe_allow_html=True
            )

    # SCORE LOCAL
    with col2:
        score_local = st.number_input("", 0, 100, 0, key="score_local")

    # SEPARADOR "vs"
    with col3:
        st.markdown("<h2 style='text-align:center'>vs</h2>", unsafe_allow_html=True)

    # SCORE VISITANTE
    with col4:
        score_away = st.number_input("", 0, 100, 0, key="score_away")

    # LOGO VISITANTE
    with col5:
        away_badge_url = st.session_state.get("away_badge_url") or ""
        if away_badge_url:
            st.markdown(
                f'<div style="text-align:center">'
                f'<img src="{away_badge_url}" width="80">'
                f'</div>',
                unsafe_allow_html=True
            )

    # OVER / UNDER
    line = st.radio("Over / Under total puntos", ["Over", "Under"], horizontal=True)

    st.markdown("**Preguntas extra:**")
    extra_1 = st.radio(pregunta_1, [local, visitante], horizontal=True, key="extra_1")
    extra_2 = st.radio(pregunta_2, [local, visitante], horizontal=True, key="extra_2")

    # SUBMIT BUTTON
    submit = st.form_submit_button("Guardar Predicción")


# -------------------------
# SUBMIT
# -------------------------
if submit:
    ganador = (
        local if score_local > score_away
        else visitante if score_away > score_local
        else "Empate"
    )

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
        "fecha_partido", "preguntas_extra",
        "preguntas_partido_id", "score_local",
        "score_away", "extra_1", "extra_2"
    ]:
        st.session_state.pop(k, None)

    st.switch_page("pages/menu_predicciones.py")
    st.stop()
