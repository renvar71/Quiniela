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

for partido in partidos:

    resultado = get_resultado_admin(partido["id_partido"])

    # 🔹 EXTRAER TEXTO DE PREGUNTAS DESDE RESULTADOS_ADMIN
    preguntas_texto = {}

    if resultado:
        r = resultado[0]

        linea = r.get("linea", "N/A")

        # Construimos diccionario de preguntas reales
        for i in range(1, 11):
            preguntas_texto[i] = r.get(f"pregunta{i}_resultado")

    else:
        linea = "N/A"
        preguntas_texto = {i: None for i in range(1, 11)}

    pred = get_prediccion_by_user(user_id, partido["id_partido"])
    if not pred:
        continue

    equipo_local = equipos_dict.get(partido["equipo_local_id"], {})
    equipo_visitante = equipos_dict.get(partido["equipo_visitante_id"], {})

    predicciones_usuario.append({
        **partido,
        **pred,
        "local": equipo_local.get("nombre", "Equipo local"),
        "visitante": equipo_visitante.get("nombre", "Equipo visitante"),
        "linea": linea,
        "preguntas_texto": preguntas_texto
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

    with col1:
        if pred.get("home_badge_url"):
            st.markdown(
                f"<div style='text-align:center'>"
                f"<img src='{pred['home_badge_url']}' width='70'>"
                f"</div>",
                unsafe_allow_html=True
            )

    with col2:
        st.number_input(
            "",
            value=pred["score_local"],
            disabled=True,
            key=f"sl_{pred['id_partido']}"
        )

    with col3:
        st.markdown("<h3 style='text-align:center'>vs</h3>", unsafe_allow_html=True)

    with col4:
        st.number_input(
            "",
            value=pred["score_away"],
            disabled=True,
            key=f"sa_{pred['id_partido']}"
        )

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

    # -------------------------
    # 🔥 PREGUNTAS EXTRA REALES
    # -------------------------
    st.markdown("**Preguntas extra:**")

    for i in range(1, 11):

        texto_pregunta = pred["preguntas_texto"].get(i)
        respuesta = pred.get(f"extra_question_{i}")

        # 👉 SOLO SI EXISTE TEXTO Y RESPUESTA
        if not texto_pregunta or not respuesta:
            continue

        st.radio(
            texto_pregunta,
            [pred["local"], pred["visitante"]],
            index=[pred["local"], pred["visitante"]].index(respuesta),
            disabled=True,
            horizontal=True,
            key=f"e{i}_{pred['id_partido']}"
        )
