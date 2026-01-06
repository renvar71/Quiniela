import streamlit as st
from datetime import datetime
from supabase_config import supabase
from db import get_prediccion_status

# -------------------------
# SESSION CHECK
# -------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

user_id = st.session_state.user_id

# -------------------------
# OBTENER PARTIDOS DESDE SUPABASE
# -------------------------
res = (
    supabase
    .table("partidos")
    .select(
        "partido_id, semana, fecha, "
        "equipos!partidos_equipo_local_id_fkey(nombre), "
        "equipos!partidos_equipo_visitante_id_fkey(nombre)"
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
    partido_id = p["partido_id"]
    semana = p["semana"]
    fecha = p["fecha"]
    local = p["equipos"]["nombre"]
    visitante = p["equipos_1"]["nombre"]

    estado = get_prediccion_status(user_id, partido_id, fecha)

    if estado == "🟡 Pendiente":
        pendientes.append((partido_id, semana, local, visitante))

# -------------------------
# UI
# -------------------------
st.title("📋 Partidos pendientes")
st.markdown("*Selecciona un partido para registrar tu predicción*")

if not pendientes:
    st.success("🎉 No tienes partidos pendientes")
else:
    for partido_id, semana, local, visitante in pendientes:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button(
                f"{local} vs {visitante}",
                key=f"p_{partido_id}",
                use_container_width=True
            ):
                st.session_state.partido_id = partido_id
                st.session_state.semana = semana
                st.session_state.local = local
                st.session_state.visitante = visitante
                st.switch_page("pages/prediccion_partido.py")
