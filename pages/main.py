# main.py
import streamlit as st
import sqlite3
import requests
from datetime import datetime, date
from db import DB, get_prediccion_status
from api import API_KEY

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
# CSS
# -------------------------
st.markdown("""
<style>
.centered-row {
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
}
.table-header {
    font-weight: bold;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# API (CACHE)
# -------------------------
@st.cache_data(ttl=300)
def get_match_result(partido_id):
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookupevent.php?id={partido_id}"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json().get("events", [])
        if not data:
            return None, None
        return data[0].get("intHomeScore"), data[0].get("intAwayScore")
    except:
        return None, None

# -------------------------
# DB
# -------------------------
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
SELECT 
    partido_id,
    semana,
    fecha,
    equipo_local_id,
    equipo_visitante_id,
    home_badge_url,
    away_badge_url,
    status
FROM partidos
ORDER BY fecha
""")

partidos = cur.fetchall()
conn.close()

today = date.today()

# -------------------------
# Determinar semana pasada y semana actual
# -------------------------
valid_dates = []
for p in partidos:
    if p[2]:
        try:
            d = datetime.fromisoformat(p[2]).date()
            if d <= today:  # partidos ya jugados o de hoy
                valid_dates.append((d, p[1]))
        except ValueError:
            continue

if valid_dates:
    prev_week = max([w for d, w in valid_dates])  # última semana con partidos hasta hoy
else:
    prev_week = max([p[1] for p in partidos]) if partidos else None

future_dates = []
for p in partidos:
    if p[2]:
        try:
            d = datetime.fromisoformat(p[2]).date()
            if d > today:
                future_dates.append((d, p[1]))
        except ValueError:
            continue

if future_dates:
    current_week = min([w for d, w in future_dates])
else:
    current_week = max([p[1] for p in partidos]) if partidos else None  # última semana

# ======================================================
# RESULTADOS SEMANA ANTERIOR (prev_week)
# ======================================================
st.subheader(f"Resultados Semana {prev_week}")

main, _ = st.columns([1, 2])

with main:
    # Headers
    h0, h1, h2, h3, h4 = st.columns([0.5, 1, 1, 1, 0.5])
    h1.markdown("<div class='table-header'>Local</div>", unsafe_allow_html=True)
    h2.markdown("<div class='table-header'>Resultado</div>", unsafe_allow_html=True)
    h3.markdown("<div class='table-header'>Visitante</div>", unsafe_allow_html=True)

    st.divider()

    # Filas
    partidos_prev = [p for p in partidos if p[1] == prev_week]
    partidos_prev.sort(key=lambda x: x[2] or "9999-12-31")  # ordenar por fecha

    for partido_id, semana, fecha,_
