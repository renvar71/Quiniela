# menu_predicciones.py
import streamlit as st
from datetime import datetime

from db import (
    get_partidos,
    get_prediccion_status
)

# -------------------------
# SESSION CHECK
# -------------------------
if not st.session_state.get("logged_in"):
    st.warning("Debes iniciar sesión")
    st.stop()

user_id = st.session_state.get("user_id")
if not user_id:
    st.stop()

# -------------------------
# OBTENER PARTIDOS (VÍA DB)
# -------------------------
partidos = get_partidos()

# -------------------------
# FILTRAR PENDIENTES
# -------------------------
pendientes = []

for p in partidos:
    id_partido = p.get("id_partido")
    semana = p.get("semana")
    fecha = p.get("fecha")

    local = p.get("equipo_local")
    visitante = p.get("equipo_visitante")

    home_badge_url = p.get("home_badge_url")
    away_badge_url = p.get("away_badge_url")

    if not id_partido or not local or not visitante:
        continue

    estado = get_prediccion_status(user_id, id_partido, fecha)

    if estado == "🟡 Pendiente":
        pendientes.append(
            (
                id_partido,
                semana,
                fecha,
                local,
                visitante,
                home_badge_url,
                away_badge_url
            )
        )

# -------------------------
# UI
# -------------------------
st.title("📋 Partidos pendientes")
st.markdown("*Selecciona un partido para registrar tu predicción*")

if not pendientes:
    st.success("🎉 No tienes partidos pendientes")
else:
    for (
        id_partido,
        semana,
        fecha,
        local,
        visitante,
        home_badge_url,
        away_badge_url
    ) in pendientes:

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button(
                f"{local} vs {visitante}",
                key=f"p_{id_partido}",
                use_container_width=True
            ):
                # limpiar contexto previo
                for k in [
                    "id_partido",
                    "semana",
                    "local",
                    "visitante",
                    "fecha_partido",
                    "home_badge_url",
                    "away_badge_url",
                ]:
                    st.session_state.pop(k, None)

                # setear nuevo contexto
                st.session_state.id_partido = id_partido
                st.session_state.semana = semana
                st.session_state.local = local
                st.session_state.visitante = visitante
                st.session_state.fecha_partido = fecha
                st.session_state.home_badge_url = home_badge_url
                st.session_state.away_badge_url = away_badge_url

                st.switch_page("pages/prediccion_partido.py")
                st.stop()
