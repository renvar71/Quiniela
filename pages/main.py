import streamlit as st
from datetime import datetime, date
import pandas as pd
import requests
from supabase_config import supabase
from db import get_prediccion_status, WEEK_TITLES

API_KEY = "TU_API_KEY"  # reemplaza con tu API_KEY de NFL
LEAGUE_ID = "4391"      # NFL

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
# 1️⃣ Poblar equipos automáticamente desde la API
# ======================================================
res = supabase.table("equipos").select("*").limit(1).execute()
if not res.data:
    try:
        r = requests.get(f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookup_all_teams.php?id={LEAGUE_ID}")
        teams = r.json().get("teams", [])
        for t in teams:
            equipo = {
                "team_id": t["idTeam"],
                "nombre": t["strTeam"],
                "badge_url": t.get("strTeamBadge"),
                "logo_url": t.get("strTeamLogo")
            }
            supabase.table("equipos").upsert(equipo, on_conflict=["team_id"]).execute()
        st.success("✅ Equipos cargados")
    except Exception as e:
        st.error(f"Error cargando equipos: {e}")

# ======================================================
# 2️⃣ Poblar partidos automáticamente desde la API
# ======================================================
res = supabase.table("partidos").select("*").limit(1).execute()
if not res.data:
    try:
        r = requests.get(f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php?id={LEAGUE_ID}")
        events = r.json().get("events", [])
        for e in events:
            partido = {
                "external_id": e["idEvent"],
                "semana": int(e.get("intRound") or 0),
                "fecha": e["dateEvent"] + "T" + e["strTime"],
                "equipo_local_id": e["idHomeTeam"],
                "equipo_visitante_id": e["idAwayTeam"],
                "home_badge_url": e.get("strHomeTeamBadge"),
                "away_badge_url": e.get("strAwayTeamBadge"),
                "tipo": "regular"
            }
            supabase.table("partidos").upsert(partido, on_conflict=["external_id"]).execute()
        st.success("✅ Partidos cargados")
    except Exception as e:
        st.error(f"Error cargando partidos: {e}")

# ======================================================
# 3️⃣ Obtener todos los partidos de Supabase
# ======================================================
partidos_res = supabase.table("partidos").select("*").execute()
partidos = partidos_res.data

today = date.today()

# -------------------------
# Determinar semana actual y previa
# -------------------------
valid_weeks = [p["semana"] for p in partidos if p["fecha"] and p["semana"] is not None and datetime.fromisoformat(p["fecha"]).date() <= today]
prev_week = max(valid_weeks) if valid_weeks else None

current_week = max([p["semana"] for p in partidos if p["semana"] is not None])

# ======================================================
# RESULTADOS SEMANA ANTERIOR
# ======================================================
if prev_week is not None:
    st.subheader(f"Resultados Semana {prev_week}")
else:
    st.subheader("Resultados recientes")

partidos_prev = [p for p in partidos if p["semana"] == prev_week]
partidos_prev.sort(key=lambda x: x["fecha"] or "9999-12-31")

data_prev = []
for p in partidos_prev:
    home_badge = p.get("home_badge_url")
    away_badge = p.get("away_badge_url")
    status = p.get("status", "scheduled")
    resultado = "—"  # opcional, si quieres mostrar marcador real

    data_prev.append({
        "Local": f'<img src="{home_badge}" width="40">' if home_badge else "",
        "Resultado": resultado,
        "Visitante": f'<img src="{away_badge}" width="40">' if away_badge else "",
        "Estado": status
    })

df_prev = pd.DataFrame(data_prev)
st.markdown(df_prev.to_html(escape=False, index=False), unsafe_allow_html=True)

# ======================================================
# PARTIDOS SEMANA ACTUAL
# ======================================================
st.subheader(WEEK_TITLES.get(current_week, f"Round / Semana {current_week}"))

partidos_next = [p for p in partidos if p["semana"] == current_week]
partidos_next.sort(key=lambda x: x["fecha"] or "9999-12-31")

data_next = []
for p in partidos_next:
    home_badge = p.get("home_badge_url")
    away_badge = p.get("away_badge_url")
    status = p.get("status", "scheduled")
    fecha_db = p.get("fecha")

    estado_pred = get_prediccion_status(st.session_state.user, p["partido_id"], fecha_db)

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
