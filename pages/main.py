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

# last week
valid_dates = []
for p in partidos:
    if p[2]: 
        try:
            d = datetime.fromisoformat(p[2]).date()
            if d < today:
                valid_dates.append(d)
        except ValueError:
            continue

prev_week = max(valid_dates) if valid_dates else None

# current_week
valid_current_dates = []
for p in partidos:
    if p[2]:
        try:
            d = datetime.fromisoformat(p[2]).date()
            if d >= today:
                valid_current_dates.append((d, p[1]))
        except ValueError:
            continue

current_week = min([w for d, w in valid_current_dates]) if valid_current_dates else None
# ======================================================
# RESULTADOS SEMANA ANTERIOR
# ======================================================
st.subheader(f"Resultados Semana {prev_week}")

main, _ = st.columns([1, 2])

with main:
    h0, h1, h2, h3, h4 = st.columns([0.3, 2, 1, 2, 0.3])
    h1.markdown("<div class='table-header'>Local</div>", unsafe_allow_html=True)
    h3.markdown("<div class='table-header'>Visitante</div>", unsafe_allow_html=True)

    st.divider()

    for partido_id, semana, fecha, _, _, home_badge, away_badge, _ in partidos:
        if semana != prev_week:
            continue

        home_score, away_score = get_match_result(partido_id)

        if home_score is None or away_score is None:
            resultado = "Sin resultado"
            home_wins = away_wins = False
        else:
            resultado = f"{home_score} - {away_score}"
            home_wins = int(home_score) > int(away_score)
            away_wins = int(away_score) > int(home_score)

        c0, c1, c2, c3, c4 = st.columns([0.3, 0.9, 1, 0.9, 0.3])

        with c0:
            if home_wins:
                st.markdown("✅")

        with c1:
            if home_badge:
                st.image(home_badge, width=40)

        with c2:
            st.markdown(f"<div class='centered-row'>{resultado}</div>", unsafe_allow_html=True)

        with c3:
            if away_badge:
                st.image(away_badge, width=40)

        with c4:
            if away_wins:
                st.markdown("✅")

# ======================================================
# PRÓXIMOS PARTIDOS
# ======================================================
st.subheader(f"Próximos partidos Semana {current_week}")

main, _ = st.columns([1, 2])

with main:
    h0, h1, h2, h3, h4 = st.columns([2, 2, 0.5, 2, 5])
    h0.markdown("<div class='table-header'>Fecha</div>", unsafe_allow_html=True)
    h1.markdown("<div class='table-header'>Local</div>", unsafe_allow_html=True)
    h3.markdown("<div class='table-header'>Visitante</div>", unsafe_allow_html=True)
    h4.markdown("<div class='table-header'>Predicción</div>", unsafe_allow_html=True)

    st.divider()

    for partido_id, semana, fecha, _, _, home_badge, away_badge, _ in partidos:
        if semana != current_week:
            continue

        estado = get_prediccion_status(
            st.session_state.user,
            partido_id,
            fecha
        )

        c0, c1, c2, c3, c4 = st.columns([2, 5, 0.5, 5, 5])

        with c0:
            fecha_fmt = datetime.fromisoformat(fecha).strftime("%d %b %Y")
            st.markdown(f"<div class='centered-row'>{fecha_fmt}</div>", unsafe_allow_html=True)

        with c1:
            if home_badge:
                st.image(home_badge, width=40)

        with c2:
            st.markdown("<div class='centered-row'>vs</div>", unsafe_allow_html=True)


        with c3:
            if away_badge:
                st.image(away_badge, width=40)

        with c4:
            st.markdown(f"<div class='centered-row'>{estado}</div>", unsafe_allow_html=True)


        
