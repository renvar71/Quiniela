import streamlit as st
from datetime import datetime, date
from db import get_partidos, get_prediccion_status, WEEK_TITLES
import pandas as pd

st.set_page_config(page_title="🏈 QUINIELA NFL 🏈")

# -------------------------
# SESSION CHECK
# -------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

st.title("🏈 QUINIELA NFL 🏈")

# -------------------------
# NAV
# -------------------------
st.divider()
col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Mis Predicciones"):
        st.switch_page("pages/menu_predicciones.py")

with col2:
    if st.button("📋 Tabla"):
        st.switch_page("pages/tabla.py")

st.divider()

# -------------------------
# CSS GLOBAL PARA TABLAS
# -------------------------
st.markdown("""
<style>
table {width: 100%; border-collapse: collapse; table-layout: fixed;}
th, td {text-align: center; vertical-align: middle; padding: 6px; font-size: 14px;}
th {font-weight: bold; background-color: #f0f0f0; color: #000; white-space: nowrap;}
td img {display: block; margin: 0 auto;}
</style>
""", unsafe_allow_html=True)

# ======================================================
# DB: obtener partidos
# ======================================================
partidos = get_partidos()  # trae todos los partidos

today = date.today()

# -------------------------
# SEMANA ACTUAL (FIX)
# -------------------------
current_week = max(
    p["semana"] for p in partidos
    if p["semana"] is not None
)

# -------------------------
# SEMANA PREVIA (para resultados)
# -------------------------
valid_weeks = [
    p["semana"] for p in partidos
    if p["fecha"] and p["semana"] is not None
    and datetime.fromisoformat(p["fecha"]).date() <= today
]

prev_week = max(valid_weeks) if valid_weeks else None

# ======================================================
# RESULTADOS
# ======================================================
if prev_week is not None:
    st.subheader(f"Resultados Semana {prev_week}")
else:
    st.subheader("Resultados recientes")

partidos_prev = [p for p in partidos if p["semana"] == prev_week]
partidos_prev.sort(key=lambda x: x["fecha"] or "9999-12-31")

data_prev = []

for p in partidos_prev:
    home_badge = p["home_badge_url"]
    away_badge = p["away_badge_url"]
    status = p["status"]
    resultado = "—"  # opcional, si tienes puntajes podrías traerlos

    data_prev.append({
        "Local": f'<img src="{home_badge}" width="40">' if home_badge else "",
        "Resultado": resultado,
        "Visitante": f'<img src="{away_badge}" width="40">' if away_badge else "",
        "Estado": status
    })

df_prev = pd.DataFrame(data_prev)
st.markdown(df_prev.to_html(escape=False, index=False), unsafe_allow_html=True)

# ======================================================
# ROUND ACTUAL (SEMANA COMPLETA)
# ======================================================
st.subheader(
    WEEK_TITLES.get(
        current_week,
        f"Round / Semana {current_week}"
    )
)

partidos_next = [p for p in partidos if p["semana"] == current_week]
partidos_next.sort(key=lambda x: x["fecha"] or "9999-12-31")

data_next = []

for p in partidos_next:
    home_badge = p["home_badge_url"]
    away_badge = p["away_badge_url"]
    status = p["status"]
    fecha_db = p["fecha"]

    estado_pred = get_prediccion_status(
        st.session_state.user,
        p["partido_id"],
        fecha_db
    )

    fecha_fmt = "To be defined"
    if fecha_db:
        try:
            fecha_fmt = datetime.fromisoformat(fecha_db).strftime("%d %b %Y")
        except ValueError:
            pass

    data_next.append({
        "Fecha": fecha_fmt,
        "Local": f'<img src="{home_badge}" width="40">' if home_badge else "",
        "vs": "vs",
        "Visitante": f'<img src="{away_badge}" width="40">' if away_badge else "",
        "Estado": status,
        "Predicción": estado_pred
    })

df_next = pd.DataFrame(data_next)
st.markdown(df_next.to_html(escape=False, index=False), unsafe_allow_html=True)
