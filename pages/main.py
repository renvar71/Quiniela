# main.py
import streamlit as st
import sqlite3
import requests
from datetime import datetime, date
from db import DB, get_prediccion_status, WEEK_TITLES
from api import API_KEY
import pandas as pd

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
table {width: 100%; border-collapse: collapse;}
th, td {text-align: center; padding: 6px; font-size: 14px;}
th {font-weight: bold; background-color: #f0f0f0;}
td img {display: block; margin: 0 auto;}
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
    status,
    tipo
FROM partidos
ORDER BY fecha

""")

partidos = cur.fetchall()
conn.close()

today = date.today()

# -------------------------
# Determinar prev_week y current_week
# -------------------------
valid_dates = []
for p in partidos:
    fecha = p[2]
    semana = p[1]

    if fecha and semana is not None:
        try:
            d = datetime.fromisoformat(fecha).date()
            if d <= today:
                valid_dates.append((d, semana))
        except ValueError:
            continue

if valid_dates:
    prev_week = max(w for d, w in valid_dates)
else:
    prev_week = None


future_dates = []
for p in partidos:
    fecha = p[2]
    semana = p[1]

    if fecha and semana is not None:
        try:
            d = datetime.fromisoformat(fecha).date()
            if d > today:
                future_dates.append((d, semana))
        except ValueError:
            continue

if future_dates:
    current_week = min(w for d, w in future_dates)
else:
    current_week = None


# -------------------------
# CSS GLOBAL PARA TABLAS
# -------------------------
st.markdown("""
<style>
table {width: 100%; border-collapse: collapse;}
th, td {text-align: center; padding: 6px; font-size: 14px;}
th {font-weight: bold; background-color: #f0f0f0; color: #000;}  /* color negro para los títulos */
td img {display: block; margin: 0 auto;}
</style>
""", unsafe_allow_html=True)

# ======================================================
# RESULTADOS SEMANA ANTERIOR
# ======================================================
if prev_week is not None:
    st.subheader(f"Resultados Semana {prev_week}")
else:
    st.subheader("Resultados recientes")


partidos_prev = [p for p in partidos if p[1] == prev_week]
partidos_prev.sort(key=lambda x: x[2] or "9999-12-31")  # ordenar por fecha

data_prev = []

for p in partidos_prev:
    partido_id = p[0]
    semana = p[1]
    fecha = p[2]
    home_badge = p[5]
    away_badge = p[6]

    home_score, away_score = get_match_result(partido_id)

    if home_score is None or away_score is None:
        resultado = "Sin resultado"
    else:
        resultado = f"{home_score} - {away_score}"

    data_prev.append({
        "Local": f'<img src="{home_badge}" width="40">' if home_badge else "",
        "Resultado": resultado,
        "Visitante": f'<img src="{away_badge}" width="40">' if away_badge else ""
    })


df_prev = pd.DataFrame(data_prev)
st.markdown(df_prev.to_html(escape=False, index=False), unsafe_allow_html=True)

# ======================================================
# PRÓXIMOS PARTIDOS
# ======================================================
if current_week is None:
    st.subheader("Próximos partidos")
else:
    st.subheader(WEEK_TITLES.get(
        current_week,
        f"Próximos partidos Semana {current_week}"
    ))

partidos_next = [p for p in partidos if p[1] == current_week]
partidos_next.sort(key=lambda x: x[2] or "9999-12-31")  # ordenar por fecha

data_next = []
for p in partidos_next:
    partido_id = p[0]
    semana = p[1]
    fecha = p[2]
    home_badge = p[5]
    away_badge = p[6]

    # Convertir fecha a formato YYYY-MM-DD para comparar con DB
    if fecha:
        try:
            fecha_fmt = datetime.fromisoformat(fecha).strftime("%d %b %Y")
            fecha_db = datetime.fromisoformat(fecha).strftime("%Y-%m-%d")
        except ValueError:
            fecha_fmt = "To be defined"
            fecha_db = None
    else:
        fecha_fmt = "To be defined"
        fecha_db = None

    # Evaluar estado según los 3 casos
    estado = get_prediccion_status(
        st.session_state.user,
        partido_id,
        fecha_db
    )

    data_next.append({
        "Fecha": fecha_fmt,
        "Local": f'<img src="{home_badge}" width="40">' if home_badge else "",
        "vs": "vs",
        "Visitante": f'<img src="{away_badge}" width="40">' if away_badge else "",
        "Predicción": estado
    })

df_next = pd.DataFrame(data_next)
st.markdown(df_next.to_html(escape=False, index=False), unsafe_allow_html=True)
