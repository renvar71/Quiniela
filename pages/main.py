import streamlit as st
from datetime import datetime, date
import pandas as pd
import requests

from supabase_config import supabase
from db import get_prediccion_status, WEEK_TITLES

#API_KEY = "TU_API_KEY"
LEAGUE_ID = "4391"  # NFL
API_URL = f"https://www.thesportsdb.com/api/v1/json/609380/lookupleague.php"

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
col1, col2= st.columns([1, 6])
with col1:
    st.image(badge_url, width=90)
with col2:
    st.title("🏈 QUINIELA NFL 🏈")

# -------------------------
# NAV
# -------------------------
#st.divider()
#col1, col2 = st.columns(2)

#with col1:
   #if st.button("📊 Mis Predicciones"):
        #st.switch_page("pages/menu_predicciones.py")

#with col2:
    #if st.button("📋 Tabla"):
        #t.switch_page("pages/tabla.py")

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
# 1️⃣ CARGAR EQUIPOS (solo si no existen)
# ======================================================
res = supabase.table("equipos").select("team_id").limit(1).execute()

if not res.data:
    try:
        r = requests.get(
            f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_teams.php?id={LEAGUE_ID}"
        )
        teams = r.json().get("teams", [])

        for t in teams:
            supabase.table("equipos").upsert({
                "team_id": t["idTeam"],
                "nombre": t["strTeam"],
                "badge_url": t.get("strTeamBadge"),
                "logo_url": t.get("strTeamLogo")
            }, on_conflict="team_id").execute()

        st.success("✅ Equipos cargados")
    except Exception as e:
        st.error(f"Error cargando equipos: {e}")

# ======================================================
# 2️⃣ CARGAR PARTIDOS (solo si no existen)
# ======================================================
res = supabase.table("partidos").select("id_partido").limit(1).execute()

if not res.data:
    try:
        r = requests.get(
            f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php?id={LEAGUE_ID}"
        )
        events = r.json().get("events", [])

        for e in events:
            fecha_iso = None
            if e.get("dateEvent") and e.get("strTime"):
                fecha_iso = f"{e['dateEvent']}T{e['strTime']}"

            supabase.table("partidos").upsert({
                "id_partido": e["idEvent"],
                "semana": int(e.get("intRound") or 0),
                "fecha": fecha_iso,
                "equipo_local_id": e["idHomeTeam"],
                "equipo_visitante_id": e["idAwayTeam"],
                "home_badge_url": e.get("strHomeTeamBadge"),
                "away_badge_url": e.get("strAwayTeamBadge"),
                "status": "scheduled"
            }, on_conflict="id_partido").execute()

        st.success("✅ Partidos cargados")
    except Exception as e:
        st.error(f"Error cargando partidos: {e}")

# ======================================================
# 3️⃣ OBTENER PARTIDOS
# ======================================================
res = supabase.table("partidos").select("*").execute()
partidos = res.data or []

if not partidos:
    st.info("No hay partidos disponibles")
    st.stop()

today = date.today()

st.markdown(
    """
    <style>
    /* Estilo general de tablas HTML */
    table {
        width: 100%;
        border-collapse: collapse;
    }

    /* Encabezados */
    table thead th {
        background-color: #e5e7eb;
        color: #111827 !important;
        font-weight: 600;
        text-align: center;
        padding: 8px;
        border-bottom: 2px solid #9ca3af;
    }

    /* Celdas */
    table tbody td {
        text-align: center;
        padding: 8px;
        border-bottom: 1px solid #d1d5db;
    }

    /* Hover */
    table tbody tr:hover {
        background-color: #f3f4f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# -------------------------
# SEMANAS
# -------------------------
past_weeks = [
    p["semana"] for p in partidos
    if p.get("fecha")
    and p.get("semana") is not None
    and datetime.fromisoformat(p["fecha"]).date() <= today
]

prev_week = max(past_weeks) if past_weeks else None
current_week = max(p["semana"] for p in partidos if p.get("semana") is not None)

# ======================================================
# RESULTADOS SEMANA ANTERIOR
# ======================================================
st.subheader(
    f"Resultados Semana {prev_week}" if prev_week is not None else "Resultados recientes"
)

partidos_prev = [p for p in partidos if p["semana"] == prev_week]

data_prev = []
for p in partidos_prev:
    data_prev.append({
        "Local": f'<img src="{p.get("home_badge_url")}" width="40">' if p.get("home_badge_url") else "",
        "Resultado": "—",
        "Visitante": f'<img src="{p.get("away_badge_url")}" width="40">' if p.get("away_badge_url") else "",
        "Estado": p.get("status", "scheduled")
    })

if data_prev:
    df_prev = pd.DataFrame(data_prev)
    st.markdown(df_prev.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("Sin resultados previos")

# ======================================================
# PARTIDOS SEMANA ACTUAL
# ======================================================
st.subheader(WEEK_TITLES.get(current_week, f"Semana {current_week}"))

partidos_next = [p for p in partidos if p["semana"] == current_week]

data_next = []
for p in partidos_next:
    fecha_db = p.get("fecha")

    estado_pred = get_prediccion_status(
        USER_ID,
        p["id_partido"],
        fecha_db
    )

    fecha_fmt = "Por definir"
    if fecha_db:
        try:
            fecha_fmt = datetime.fromisoformat(fecha_db).strftime("%d %b %Y")
        except ValueError:
            pass

    data_next.append({
        "Fecha": fecha_fmt,
        "Local": f'<img src="{p.get("home_badge_url")}" width="40">' if p.get("home_badge_url") else "",
        "vs": "vs",
        "Visitante": f'<img src="{p.get("away_badge_url")}" width="40">' if p.get("away_badge_url") else "",
        "Estado": p.get("status", "scheduled"),
        "Predicción": estado_pred
    })

df_next = pd.DataFrame(data_next)
st.markdown(df_next.to_html(escape=False, index=False), unsafe_allow_html=True)
