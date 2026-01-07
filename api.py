# api.py
import requests
import streamlit as st

from db import (
    save_team,
    upsert_partidos,
    get_team_id_by_name
)

API_KEY = "609380"
LEAGUE_ID = 4391


@st.cache_data
def get_team_badges():
    """Devuelve un diccionario {team_id: badge_url} para todos los equipos."""
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/search_all_teams.php?l=NFL"
    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        return {}

    teams = r.json().get("teams", []) or []

    return {
        t["idTeam"]: t["strTeamBadge"]
        for t in teams
        if t.get("idTeam") and t.get("strTeamBadge")
    }


def save_teams():
    """Obtiene equipos del API y los guarda en la BD."""
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/search_all_teams.php?l=NFL"
    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        print("❌ Error al obtener equipos:", r.status_code)
        return

    teams = r.json().get("teams", []) or []

    equipos = []
    for t in teams:
        if not t.get("idTeam") or not t.get("strTeam") or not t.get("strTeamBadge"):
            continue

        equipos.append({
            "team_id": t["idTeam"],
            "nombre": t["strTeam"],
            "badge_url": t["strTeamBadge"]
        })

    if equipos:
        save_team(equipos)


def save_next_games():
    """Obtiene próximos partidos y los guarda en la BD."""
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php?id={LEAGUE_ID}"
    r = requests.get(url, timeout=10)

    if r.status_code != 200:
        print("⚠️ Error al obtener partidos:", r.status_code)
        return []

    events = (r.json() or {}).get("events") or []

    if not events:
        print("⏳ No hay partidos programados aún")
        return []

    partidos = []
    for g in events:
        if not g.get("idEvent") or not g.get("idHomeTeam") or not g.get("idAwayTeam"):
            continue

        partidos.append({
            "id_partido": g["idEvent"],
            "external_id": g["idEvent"],
            "semana": g.get("intRound"),
            "fecha": g.get("dateEvent"),
            "equipo_local_id": g["idHomeTeam"],
            "equipo_visitante_id": g["idAwayTeam"],
            "home_badge_url": g.get("strHomeTeamBadge"),
            "away_badge_url": g.get("strAwayTeamBadge"),
            "estadio": g.get("strVenue"),
            "status": g.get("strStatus") or "NS"
        })

    if partidos:
        upsert_partidos(partidos)

    return events
