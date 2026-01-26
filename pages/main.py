# main.py
import streamlit as st
from datetime import datetime, date
import pandas as pd
import requests
from db import get_prediccion_status, WEEK_TITLES, get_supabase
from zoneinfo import ZoneInfo 

# -------------------------
# CONFIG
# -------------------------
LEAGUE_ID = "4391"  # NFL
API_KEY = 609380
API_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookupleague.php"

SEMANA_ACTIVA = 200

st.set_page_config(page_title="🏈 QUINIELA NFL 🏈", layout="wide")

# -------------------------
# SESSION CHECK
# -------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

USER_ID = st.session_state.user_id

# -------------------------
# NFL LEAGUE BADGE
# -------------------------
@st.cache_data
def get_nfl_badge():
    r = requests.get(API_URL, params={"id": LEAGUE_ID}, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data["leagues"][0]["strBadge"]

badge_url = get_nfl_badge()

# -------------------------
# HEADER
# -------------------------
col1, col2 = st.columns([1, 6])
with col1:
    st.image(badge_url, width=90)
with col2:
    st.title("🏈 QUINIELA NFL 🏈")

st.divider()

# -------------------------
# CSS
# -------------------------
st.markdown("""
<style>
table {width: 100%; border-collapse: collapse;}
th, td {text-align: center; padding: 6px; font-size: 14px;}
th {background-color: #f0f0f0;}
td img {display: block; margin: 0 auto;}
</style>
""", unsafe_allow_html=True)

# ======================================================
# CARGAR PARTIDOS (pasados y futuros)
# ======================================================
def cargar_partidos():
    endpoints = [
        ("past", f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventspastleague.php?id={LEAGUE_ID}"),
        ("next", f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php?id={LEAGUE_ID}")
    ]

    supabase = get_supabase()

    for tipo, url in endpoints:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            events = r.json().get("events", [])

            for e in events:
                fecha_iso = None
                if e.get("dateEvent") and e.get("strTime"):
                    fecha_iso = f"{e['dateEvent']}T{e['strTime']}"

                status = "finished" if tipo == "past" else "scheduled"

                supabase.table("partidos").upsert({
                    "id_partido": e["idEvent"],
                    "semana": int(e.get("intRound") or 0),
                    "fecha": fecha_iso,
                    "equipo_local_id": e["idHomeTeam"],
                    "equipo_visitante_id": e["idAwayTeam"],
                    "home_badge_url": e.get("strHomeTeamBadge"),
                    "away_badge_url": e.get("strAwayTeamBadge"),
                    "score_local": e.get("intHomeScore"),
                    "score_away": e.get("intAwayScore"),
                    "status": status
                }, on_conflict="id_partido").execute()

        except Exception as e:
            st.error(f"Error cargando partidos {tipo}: {e}")

# Sincronizar siempre que cambie la semana activa
if st.session_state.get("ultima_semana_cargada") != SEMANA_ACTIVA:
    cargar_partidos()
    st.session_state.ultima_semana_cargada = SEMANA_ACTIVA

# ======================================================
# OBTENER PARTIDOS
# ======================================================
supabase = get_supabase()
res = supabase.table("partidos").select("*").execute()
partidos = res.data or []

if not partidos:
    st.info("No hay partidos disponibles")
    st.stop()

# ======================================================
# FILTRAR POR SEMANA MANUAL
# ======================================================
partidos_semana = [
    p for p in partidos
    if p.get("semana") == SEMANA_ACTIVA
]

semana_nombre = WEEK_TITLES.get(SEMANA_ACTIVA, f"Semana {SEMANA_ACTIVA}")
st.subheader(semana_nombre)

# ======================================================
# PARTIDOS FUTUROS
# ======================================================
futuros = [p for p in partidos_semana if not p.get("confirmed_result")]

data_futuros = []
for p in futuros:
    fecha_db = p.get("fecha")
    estado_pred_raw = get_prediccion_status(USER_ID, p["id_partido"], fecha_db)

    if estado_pred_raw == "🔴 Expirada":
        existe_pred = (
            supabase
            .table("predicciones")
            .select("id")
            .eq("usuario_id", USER_ID)
            .eq("id_partido", p["id_partido"])
            .limit(1)
            .execute()
        )
        estado_pred = "🟢 Registrada" if existe_pred.data else "🔴 Expirada"
    else:
        estado_pred = estado_pred_raw

    fecha_fmt = "Por definir"
    if fecha_db:
        try:
            fecha_utc = datetime.fromisoformat(fecha_db).replace(tzinfo=ZoneInfo("UTC"))
            fecha_cst = fecha_utc.astimezone(ZoneInfo("America/Mexico_City"))
            fecha_fmt = fecha_cst.strftime("%d %b %Y %H:%M")
        except ValueError:
            pass

    data_futuros.append({
        "Fecha": fecha_fmt,
        "Local": f'<img src="{p.get("home_badge_url")}" width="40">' if p.get("home_badge_url") else "",
        "vs": "vs",
        "Visitante": f'<img src="{p.get("away_badge_url")}" width="40">' if p.get("away_badge_url") else "",
        "Predicción": estado_pred
    })

if data_futuros:
    df_futuros = pd.DataFrame(data_futuros)
    st.markdown(df_futuros.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("No hay partidos próximos para esta semana")

# ======================================================
# PARTIDOS PASADOS
# ======================================================
completados = [p for p in partidos_semana if p.get("confirmed_result")]

data_completados = []
for p in completados:
    data_completados.append({
        "Local": f'<img src="{p.get("home_badge_url")}" width="40">' if p.get("home_badge_url") else "",
        "Resultado": f"{p.get('score_local', 0)} - {p.get('score_away', 0)}",
        "Visitante": f'<img src="{p.get("away_badge_url")}" width="40">' if p.get("away_badge_url") else ""
    })

if data_completados:
    df_completados = pd.DataFrame(data_completados)
    st.subheader("Partidos completados")
    st.markdown(df_completados.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("")
