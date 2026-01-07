# prediccion_partido.py
import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os
from api import get_team_badges
from db import save_prediccion, WEEK_TITLES, get_resultado_admin

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

if "prediccion_enviada" not in st.session_state:
    st.session_state.prediccion_enviada = False
# -------------------------
# VALIDAR CONTEXTO REAL
# -------------------------
required_keys = [
    "id_partido", "semana", "local",
    "visitante", "fecha_partido"
]

if not all(st.session_state.get(k) is not None for k in required_keys):
    for k in required_keys:
        st.session_state.pop(k, None)
    st.switch_page("pages/menu_predicciones.py")
    st.stop()

id_partido = st.session_state.id_partido
semana = st.session_state.semana
local = st.session_state.local
visitante = st.session_state.visitante
fecha_partido = st.session_state.fecha_partido

team_badges = get_team_badges()

# -------------------------
# LOAD PREGUNTAS (CACHE)
# -------------------------
@st.cache_data
def load_preguntas():
    df = pd.read_csv("preguntas.csv")
    return df["pregunta"].dropna().tolist()

# -------------------------
# PREGUNTAS EXTRA
# -------------------------
if (
    "preguntas_extra" not in st.session_state
    or st.session_state.get("preguntas_id_partido") != id_partido
):
    preguntas = load_preguntas()
    random.seed(id_partido)
    st.session_state.preguntas_extra = random.sample(preguntas, 2)
    st.session_state.preguntas_id_partido = id_partido

pregunta_1, pregunta_2 = st.session_state.preguntas_extra

# -------------------------
# RESULTADO ADMIN (CACHE SESSION)
# -------------------------
if (
    "resultado_admin" not in st.session_state
    or st.session_state.get("resultado_admin_id") != id_partido
):
    st.session_state.resultado_admin = get_resultado_admin(id_partido)
    st.session_state.resultado_admin_id = id_partido

resultado_admin = st.session_state.resultado_admin

# -------------------------
# NAV BACK
# -------------------------
if st.button("⬅️ Volver"):
    for k in [
        "id_partido", "semana", "local", "visitante",
        "fecha_partido", "preguntas_extra",
        "preguntas_id_partido", "resultado_admin",
        "resultado_admin_id", "score_local",
        "score_away", "extra_1", "extra_2",
        "prediccion_enviada"
    ]:
        st.session_state.pop(k, None)

    st.switch_page("pages/menu_predicciones.py")
    st.stop()

# -------------------------
# UI
# -------------------------
st.title("🎯 Registrar predicción")
st.subheader(WEEK_TITLES.get(semana, f"Semana {semana}"))
st.write(f"**{local} vs {visitante}**")

# -------------------------
# FORM
# -------------------------
with st.form("form_prediccion"):

    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])

    with col1:
        home_badge_url = st.session_state.get("home_badge_url")
        if home_badge_url:
            st.markdown(
                f'<div style="text-align:center">'
                f'<img src="{home_badge_url}" width="80">'
                f'</div>',
                unsafe_allow_html=True
            )

    with col2:
        score_local = st.number_input("", 0, 100, 0, key="score_local")

    with col3:
        st.markdown("<h2 style='text-align:center'>vs</h2>", unsafe_allow_html=True)

    with col4:
        score_away = st.number_input("", 0, 100, 0, key="score_away")

    with col5:
        away_badge_url = st.session_state.get("away_badge_url")
        if away_badge_url:
            st.markdown(
                f'<div style="text-align:center">'
                f'<img src="{away_badge_url}" width="80">'
                f'</div>',
                unsafe_allow_html=True
            )

    if resultado_admin:
        linea = resultado_admin[0].get("linea")
    else:
        linea = "N/A"

    line = st.radio(
        f"Over / Under total puntos ({linea})",
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
# SUBMIT
# -------------------------
if submit:

    if st.session_state.get("prediccion_enviada"):
        st.stop()

    st.session_state.prediccion_enviada = True

    ganador = (
        local if score_local > score_away
        else visitante if score_away > score_local
        else "Empate"
    )

    save_prediccion(
        usuario_id=user_id,
        id_partido=id_partido,
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
        "id_partido", "semana", "local", "visitante",
        "fecha_partido", "preguntas_extra",
        "preguntas_id_partido",
        "score_local", "score_away",
        "extra_1", "extra_2"
    ]:
        st.session_state.pop(k, None)

    st.switch_page("pages/menu_predicciones.py")
    st.stop()
