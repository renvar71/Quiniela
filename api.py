# api.py
import requests
import streamlit as st
from db import supabase

API_KEY = "609380"
LEAGUE_ID = 4391

@st.cache_data
def get_team_badges():
    """Devuelve un diccionario {team_id: badge_url} para todos los equipos."""
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/search_all_teams.php?l=NFL"
    r = requests.get(url)

    if r.status_code != 200:
        return {}

    data = r.json()
    teams = data.get("teams", [])

    badges = {}
    for t in teams:
        team_id = t.get("idTeam")
        badge = t.get("strTeamBadge")
        if team_id and badge:
            badges[team_id] = badge

    return badges


def save_teams():
    """Guarda los equipos en Supabase."""
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/search_all_teams.php?l=NFL"
    r = requests.get(url)

    if r.status_code != 200:
        print("Error al obtener equipos:", r.status_code)
        return

    teams = r.json().get("teams", [])

    for t in teams:
        team_id = t.get("idTeam")
        nombre = t.get("strTeam")
        badge = t.get("strTeamBadge")

        # Validar datos antes de insertar
        if not team_id or not nombre or not badge:
            continue

        supabase.table("equipos").upsert([{
            "team_id": team_id,
            "nombre": nombre,
            "badge_url": badge
        }], on_conflict=["team_id"]).execute()


def save_next_games():
    """Guarda los próximos partidos en Supabase usando IDs de equipos y badges."""
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php?id={LEAGUE_ID}"
    r = requests.get(url)

    if r.status_code != 200:
        print("⚠️ Error al obtener partidos:", r.status_code)
        return []

    data = r.json() or {}
    events = data.get("events")

    # API aún sin agenda
    if not events:
        print("⏳ Esperando agenda de próximos partidos...")
        return []

    for g in events:
        if not g.get("idEvent") or not g.get("idHomeTeam") or not g.get("idAwayTeam"):
            continue

        supabase.table("partidos").upsert([{
            "partido_id": g.get("idEvent"),
            "external_id": g.get("idEvent"),
            "semana": g.get("intRound"),
            "fecha": g.get("dateEvent"),
            "equipo_local_id": g.get("idHomeTeam"),
            "equipo_visitante_id": g.get("idAwayTeam"),
            "home_badge_url": g.get("strHomeTeamBadge"),
            "away_badge_url": g.get("strAwayTeamBadge"),
            "estadio": g.get("strVenue"),
            "status": g.get("strStatus") or "NS"
        }], on_conflict=["partido_id"]).execute()

    return events

def get_team_id_by_name(name):
    """Devuelve el team_id dado el nombre del equipo."""
    res = supabase.table("equipos").select("team_id").eq("nombre", name).single().execute()
    return res.data["team_id"] if res.data else None
