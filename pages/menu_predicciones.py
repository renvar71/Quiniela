#menu_predicciones
import streamlit as st
from supabase_config import supabase
from db import get_prediccion_status, get_prediccion_by_user

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
# CONTEXT + NAV
# -------------------------
def _set_context_and_go(p):
    for k in [
        "id_partido", "semana", "local", "visitante",
        "fecha_partido", "home_badge_url", "away_badge_url",
        "edit_mode", "prediccion_actual"
    ]:
        st.session_state.pop(k, None)

    st.session_state.id_partido = p["id_partido"]
    st.session_state.semana = p["semana"]
    st.session_state.local = p["local"]
    st.session_state.visitante = p["visitante"]
    st.session_state.fecha_partido = p["fecha"]
    st.session_state.home_badge_url = p["home_badge_url"]
    st.session_state.away_badge_url = p["away_badge_url"]

    st.session_state.edit_mode = bool(p["prediccion"])
    st.session_state.prediccion_actual = p["prediccion"]

    st.switch_page("pages/prediccion_partido.py")
    st.stop()
# -------------------------
# OBTENER PARTIDOS
# -------------------------
res = (
    supabase
    .table("partidos")
    .select(
        """
        id_partido,
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

pendientes = []
completados = []

for p in partidos:
    id_partido = p.get("id_partido")
    semana = p.get("semana")
    fecha = p.get("fecha")
    local = p.get("local", {}).get("nombre")
    visitante = p.get("visitante", {}).get("nombre")

    if not id_partido or not local or not visitante:
        continue

    estado = get_prediccion_status(user_id, id_partido, fecha)
    prediccion = get_prediccion_by_user(user_id, id_partido)

    item = {
        "id_partido": id_partido,
        "semana": semana,
        "fecha": fecha,
        "local": local,
        "visitante": visitante,
        "home_badge_url": p.get("home_badge_url"),
        "away_badge_url": p.get("away_badge_url"),
        "prediccion": prediccion
    }

    if estado == "🟡 Pendiente":
        pendientes.append(item)
    else:
        completados.append(item)

# -------------------------
# UI
# -------------------------
st.title("📋 Partidos")
st.markdown("📝 **Haz click para editar un partido**")

col_pend, col_comp = st.columns(2)

# -------------------------
# PENDIENTES
# -------------------------
with col_pend:
    st.subheader("🟡 Pendientes")

    if not pendientes:
        st.info("No tienes partidos pendientes")

    for p in pendientes:
        label = f"{p['local']} vs {p['visitante']}"

        if st.button(label, key=f"pend_{p['id_partido']}", use_container_width=True):
            _set_context_and_go(p)

# -------------------------
# COMPLETADOS
# -------------------------
with col_comp:
    st.subheader("🟢 Completados")

    if not completados:
        st.info("Aún no has completado predicciones")

    for p in completados:
        label = f"{p['local']} vs {p['visitante']}"

        if st.button(label, key=f"comp_{p['id_partido']}", use_container_width=True):
            _set_context_and_go(p)


