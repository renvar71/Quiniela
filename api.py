# api.py
import requests
import sqlite3
from db import DB
import streamlit as st

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
    """Guarda los equipos en la base de datos."""
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/search_all_teams.php?l=NFL"
    r = requests.get(url)

    if r.status_code != 200:
        print("Error teams:", r.status_code)
        return

    data = r.json()
    teams = data.get("teams", [])

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    for t in teams:
        cur.execute("""
            INSERT OR IGNORE INTO equipos (team_id, nombre, badge_url)
            VALUES (?, ?, ?)
        """, (
            t.get("idTeam"),
            t.get("strTeam"),
            t.get("strTeamBadge")
        ))

    conn.commit()
    conn.close()


def save_next_games():
    """Guarda los próximos partidos en la base de datos usando IDs de equipos y badges."""
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php?id={LEAGUE_ID}"
    r = requests.get(url)

    if r.status_code != 200:
        print("Error al obtener partidos:", r.status_code)
        return

    events = r.json().get("events", [])

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    for g in events:
        cur.execute("""
            INSERT OR REPLACE INTO partidos (
                partido_id, external_id, semana, fecha,
                equipo_local_id, equipo_visitante_id,
                home_badge_url, away_badge_url,
                estadio, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            g.get("idEvent"),
            g.get("idEvent"),
            g.get("intRound"),
            g.get("dateEvent"),
            g.get("idHomeTeam"),
            g.get("idAwayTeam"),
            g.get("strHomeTeamBadge"),
            g.get("strAwayTeamBadge"),
            g.get("strVenue"),
            g.get("strStatus") or 'NS'
        ))

    conn.commit()
    conn.close()


def get_team_id_by_name(cur, name):
    """Devuelve el team_id dado el nombre del equipo."""
    cur.execute(
        "SELECT team_id FROM equipos WHERE nombre = ?",
        (name,)
    )
    row = cur.fetchone()
    return row[0] if row else None
