#menu_predicciones.py
import streamlit as st
# Cambio 1
# from supabase_config import supabase
# from db import get_prediccion_status, get_prediccion_by_user, WEEK_TITLES, get_supabase, get_prediccion_by_user_optimized
from db import WEEK_TITLES, get_supabase, get_prediccion_by_user_optimized
# -------------------------
# SESSION CHECK
# -------------------------
if not st.session_state.get("logged_in"):
    st.warning("Debes iniciar sesión")
    st.stop()

user_id = st.session_state.get("user_id")
if not user_id:
    st.stop()

# Uso de nueva función similar para revisar si las predicciones ya se encuentran en cache
if "predicciones_cache" not in st.session_state:
    preds = get_prediccion_by_user_optimized(user_id)

    # indexar por id_partido
    st.session_state.predicciones_cache = {
        p["id_partido"]: p for p in preds
    }

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
# Cambio 2
# Cacheamos para que no se carguen cada vez que se hace una visita a la pagina
# res = (
#     supabase
#     .table("partidos")
#     .select(
#         """
#         id_partido,
#         semana,
#         fecha,
#         local:equipos!partidos_equipo_local_id_fkey(nombre, badge_url),
#         visitante:equipos!partidos_equipo_visitante_id_fkey(nombre, badge_url),
#         home_badge_url,
#         away_badge_url
#         """
#     )
#     .order("fecha")
#     .execute()
# )

# partidos = res.data or []
if "partidos_cache" not in st.session_state:
    supabase = get_supabase()

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

    st.session_state.partidos_cache = res.data or []

# usar SIEMPRE desde sesión
partidos = st.session_state.partidos_cache
# -------------------------
# FILTRAR POR SEMANA MÁS ALTA
# -------------------------
if partidos:
    max_semana = max(p.get("semana", 0) for p in partidos)
    partidos = [p for p in partidos if p.get("semana") == max_semana]
else:
    max_semana = None

# -------------------------
# SEPARAR PENDIENTES Y COMPLETADOS
# -------------------------
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
    # Quitamos llamadas dentro del loop   
    # estado = (user_id, id_partido, fecha)
    # prediccion = get_prediccion_by_user(user_id, id_partido)
    predicciones = st.session_state.predicciones_cache
    prediccion = predicciones.get(id_partido)

    estado = "🟡 Pendiente"
    if prediccion:
        estado = "🟢 Completado"


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
if max_semana:
    semana_nombre = WEEK_TITLES.get(max_semana, f"Semana {max_semana}")
    st.title(f"📋 Partidos - {semana_nombre}")
else:
    st.title("📋 Partidos")

col_pend, col_comp = st.columns(2)

# -------------------------
# PENDIENTES
# -------------------------
with col_pend:
    st.subheader("Pendientes 🟡")
    st.markdown("*Selecciona el partido que quieras registrar*")

    if not pendientes:
        st.info("No hay predicciones pendientes")

    for p in pendientes:
        label = f"{p['local']} vs {p['visitante']}"

        if st.button(label, key=f"pend_{p['id_partido']}", use_container_width=True):
            _set_context_and_go(p)

# -------------------------
# COMPLETADOS
# -------------------------
with col_comp:
    st.subheader("Completados 🟢")
    st.markdown("*Selecciona el partido que quieras editar*")

    if not completados:
        st.info("¡Llena tu primera predicción")

    for p in completados:
        label = f"{p['local']} vs {p['visitante']}"

        if st.button(label, key=f"comp_{p['id_partido']}", use_container_width=True):
            _set_context_and_go(p)
