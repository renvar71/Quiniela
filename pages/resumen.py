# resumen.py
import streamlit as st
import random
import pandas as pd
from db import (
    get_partidos,
    get_prediccion_by_user,
    get_equipos,
    WEEK_TITLES,
    get_resultado_admin
)

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
# DATA BASE
# -------------------------
equipos = get_equipos()
equipos_dict = {e["team_id"]: e for e in equipos}

partidos = get_partidos()
predicciones_usuario = []

def get_preguntas_por_partido(id_partido):
    df = pd.read_csv("preguntas.csv")
    preguntas = df["pregunta"].dropna().tolist()

    random.seed(id_partido)
    return random.sample(preguntas, 2)


for partido in partidos:
    
    resultado = get_resultado_admin(partido["id_partido"])

    if resultado:
        linea = resultado[0].get("linea")
    else:
        linea = "N/A"

    pred = get_prediccion_by_user(user_id, partido["id_partido"])
    if not pred:
        continue

    equipo_local = equipos_dict.get(partido["equipo_local_id"], {})
    equipo_visitante = equipos_dict.get(partido["equipo_visitante_id"], {})
    pregunta_1, pregunta_2 = get_preguntas_por_partido(partido["id_partido"])


    predicciones_usuario.append({
        **partido,
        **pred,
        "local": equipo_local.get("nombre", "Equipo local"),
        "visitante": equipo_visitante.get("nombre", "Equipo visitante"),
        "pregunta_1": pregunta_1,
        "pregunta_2": pregunta_2,
        "linea": linea
    })


# -------------------------
# UI
# -------------------------
st.title("📊 Resumen de Mis Predicciones")

if not predicciones_usuario:
    st.info("Todavía no tienes predicciones registradas")

    if st.button("🎯 Registrar mi primera predicción"):
        st.switch_page("pages/menu_predicciones.py")

    st.stop()

# -------------------------
# LISTADO
# -------------------------
for pred in predicciones_usuario:

    st.divider()

    st.subheader(WEEK_TITLES.get(pred["semana"], f"Semana {pred['semana']}"))
    st.write(f"**{pred['local']} vs {pred['visitante']}**")
    st.caption(pred["fecha"])

    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])

    # LOGO LOCAL
    with col1:
        if pred.get("home_badge_url"):
            st.markdown(
                f"<div style='text-align:center'>"
                f"<img src='{pred['home_badge_url']}' width='70'>"
                f"</div>",
                unsafe_allow_html=True
            )

    # SCORE LOCAL
    with col2:
        st.number_input(
            "",
            value=pred["score_local"],
            disabled=True,
            key=f"sl_{pred['id_partido']}"
        )

    # VS
    with col3:
        st.markdown("<h3 style='text-align:center'>vs</h3>", unsafe_allow_html=True)

    # SCORE VISITANTE
    with col4:
        st.number_input(
            "",
            value=pred["score_away"],
            disabled=True,
            key=f"sa_{pred['id_partido']}"
        )

    # LOGO VISITANTE
    with col5:
        if pred.get("away_badge_url"):
            st.markdown(
                f"<div style='text-align:center'>"
                f"<img src='{pred['away_badge_url']}' width='70'>"
                f"</div>",
                unsafe_allow_html=True
            )

    # OVER / UNDER
    st.radio(
        f"Over / Under total puntos ({pred['linea']})",
        ["Over", "Under"],
        index=["Over", "Under"].index(pred["line_over_under"]),
        disabled=True,
        horizontal=True,
        key=f"ou_{pred['id_partido']}"
    )

    # PREGUNTAS EXTRA
    st.markdown("**Preguntas extra:**")

    st.radio(
        pred["pregunta_1"],
        [pred["local"], pred["visitante"]],
        index=[pred["local"], pred["visitante"]].index(pred["extra_question_1"]),
        disabled=True,
        horizontal=True,
        key=f"e1_{pred['id_partido']}"
    )

    st.radio(
        pred["pregunta_2"],
        [pred["local"], pred["visitante"]],
        index=[pred["local"], pred["visitante"]].index(pred["extra_question_2"]),
        disabled=True,
        horizontal=True,
        key=f"e2_{pred['id_partido']}"
    )
