#prediccion_partido.py
import streamlit as st
import pandas as pd
import random
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

# -------------------------
# VALIDAR CONTEXTO
# -------------------------
required_keys = [
    "id_partido", "semana", "local",
    "visitante", "fecha_partido"
]

if not all(st.session_state.get(k) is not None for k in required_keys):
    st.switch_page("pages/menu_predicciones.py")
    st.stop()

id_partido = st.session_state.id_partido
semana = st.session_state.semana
local = st.session_state.local
visitante = st.session_state.visitante
fecha_partido = st.session_state.fecha_partido

edit_mode = st.session_state.get("edit_mode", False)
pred = st.session_state.get("prediccion_actual")

# -------------------------
# PREGUNTAS EXTRA
# -------------------------
if (
    "preguntas_extra" not in st.session_state
    or st.session_state.get("preguntas_id_partido") != id_partido
):
    df = pd.read_csv("preguntas.csv")
    preguntas = df["pregunta"].dropna().tolist()
    random.seed(id_partido)
    st.session_state.preguntas_extra = random.sample(preguntas, 2)
    st.session_state.preguntas_id_partido = id_partido

pregunta_1, pregunta_2 = st.session_state.preguntas_extra

if st.button("🔙 Volver"):
    st.switch_page("pages/menu_predicciones.py")
# -------------------------
# UI
# -------------------------
st.title("✏️ Editar predicción" if edit_mode else "🎯 Registrar predicción")
st.subheader(WEEK_TITLES.get(semana, f"Semana {semana}"))
st.write(f"**{local} vs {visitante}**")

# -------------------------
# FORM
# -------------------------
with st.form("form_prediccion"):

    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])

    # LOGO LOCAL
    with col1:
        home_badge_url = st.session_state.get("home_badge_url")
        if home_badge_url:
            st.markdown(
                f'<div style="text-align:center">'
                f'<img src="{home_badge_url}" width="80">'
                f'</div>',
                unsafe_allow_html=True
            )

      # SCORE LOCAL
    with col2:
        score_local = st.number_input(
            "",
            0,
            100,
            value=pred["score_local"] if edit_mode and pred else 0,
            key="score_local"
        )

    # SEPARADOR "vs"
    with col3:
        st.markdown("<h2 style='text-align:center'>vs</h2>", unsafe_allow_html=True)

    # SCORE VISITANTE
    with col4:
        score_away = st.number_input(
            "",
            0,
            100,
            value=pred["score_away"] if edit_mode and pred else 0,
            key="score_away"
        )

    # LOGO VISITANTE
    with col5:
        away_badge_url = st.session_state.get("away_badge_url")
        if away_badge_url:
            st.markdown(
                f'<div style="text-align:center">'
                f'<img src="{away_badge_url}" width="80">'
                f'</div>',
                unsafe_allow_html=True
            )

    # OVER / UNDER
    # id_partido ya viene de st.session_state
    resultado = get_resultado_admin(id_partido)

    if resultado:
        linea = resultado[0]["linea"]
    else:
        st.write("No se encontró información del partido")
        linea = "N/A"  # para evitar error si no hay valor
    
    line = st.radio(
        f"Over / Under total puntos ({linea})",
        ["Over", "Under"],
        index=["Over", "Under"].index(pred["line_over_under"]) if edit_mode and pred else 0,
        horizontal=True,
        key="linea"
    )

    # PREGUNTAS EXTRA
    pregunta_1, pregunta_2 = st.session_state.preguntas_extra
    st.markdown("**Preguntas extra:**")

    # PREGUNTAS EXTRA
     extra_1 = st.radio(
        pregunta_1,
        [local, visitante],
        index=[local, visitante].index(pred["extra_question_1"]) if edit_mode and pred else 0,
        horizontal=True,
        key="extra_1"
    )

    extra_2 = st.radio(
        pregunta_2,
        [local, visitante],
        index=[local, visitante].index(pred["extra_question_2"]) if edit_mode and pred else 0,
        horizontal=True,
        key="extra_2"
    )

    submit = st.form_submit_button(
        "Actualizar Predicción" if edit_mode else "Guardar Predicción"
    )

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

    st.success("✅ Predicción actualizada" if edit_mode else "✅ Predicción guardada")

    for k in list(st.session_state.keys()):
        if k not in ["logged_in", "user_id","user"]:
            st.session_state.pop(k)

    st.switch_page("pages/menu_predicciones.py")
    st.stop()
