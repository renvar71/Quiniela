# menu_predicciones.py
import streamlit as st
from datetime import datetime
from supabase_config import supabase
from db import get_prediccion_status

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
# OBTENER PARTIDOS
# -------------------------
res = (
    supabase
    .table("partidos")
    .select(
        """
        partido_id,
        semana,
        fecha,
        local:equipos!partidos_equipo_local_id_fkey(nombre, badge_url),
        visitante:equipos!partidos_equipo_visitante_id_fkey(nombre, badge_url),
        home_badge_url,
        away_badge_url
        """
    )
    .order("fecha")
    .execute()
)

partidos = res.data or []

# -------------------------
# FILTRAR PENDIENTES
# -------------------------
pendientes = []

for p in partidos:
    partido_id = p.get("partido_id")
    semana = p.get("semana")
    fecha = p.get("fecha")

    local = p.get("local", {}).get("nombre")
    visitante = p.get("visitante", {}).get("nombre")

    if not partido_id or not local or not visitante:
        continue

    estado = get_prediccion_status(user_id, partido_id, fecha)

    if estado == "🟡 Pendiente":
        pendientes.append((partido_id, semana, fecha, local, visitante, p.get("home_badge_url"), p.get("away_badge_url")))

# -------------------------
# UI
# -------------------------
st.title("📋 Partidos pendientes")
st.markdown("*Selecciona un partido para registrar tu predicción*")

if not pendientes:
    st.success("🎉 No tienes partidos pendientes")
else:
    for partido_id, semana, fecha, local, visitante, home_badge_url, away_badge_url in pendientes:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button(
                f"{local} vs {visitante}",
                key=f"p_{partido_id}",
                use_container_width=True
            ):
                # limpiar contexto previo
                for k in [
                    "partido_id", "semana", "local",
                    "visitante", "fecha_partido",
                    "home_badge_url", "away_badge_url"
                ]:
                    st.session_state.pop(k, None)

                # setear nuevo contexto con badges incluidos
                st.session_state.partido_id = partido_id
                st.session_state.semana = semana
                st.session_state.local = local
                st.session_state.visitante = visitante
                st.session_state.fecha_partido = fecha
                st.session_state.home_badge_url = home_badge_url
                st.session_state.away_badge_url = away_badge_url

                st.switch_page("pages/prediccion_partido.py")
                st.stop()
