# resumen.py
import streamlit as st
from db import get_prediccion_by_user, WEEK_TITLES

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
# DATA
# -------------------------
predicciones = get_prediccion_by_user(user_id)

# -------------------------
# UI
# -------------------------
st.title("📊 Mis Predicciones")

if not predicciones:
    st.info("Todavía no tienes predicciones registradas")

    if st.button("Registra tu primera predicciñon y la podrás ver aquí"):
        st.switch_page("pages/prediccion_partido.py")

    st.stop()

# -------------------------
# LISTADO DE PREDICCIONES
# -------------------------
for pred in predicciones:

    st.divider()

    st.subheader(WEEK_TITLES.get(pred["semana"], f"Semana {pred['semana']}"))
    st.write(f"**{pred['local']} vs {pred['visitante']}**")
    st.caption(pred["fecha_partido"])

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
