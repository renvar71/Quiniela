import requests
import sqlite3
from db import DB
from api import API_KEY


# -------------------------
# RESULTADO REAL DEL PARTIDO
# -------------------------
def fetch_match_result(partido_id):
    """
    Obtiene marcador final desde TheSportsDB
    """
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookupevent.php?id={partido_id}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()

    data = r.json().get("events", [])
    if not data:
        return None

    e = data[0]

    score_local = e.get("intHomeScore")
    score_away = e.get("intAwayScore")

    if score_local is None or score_away is None:
        return None  # partido no finalizado

    return {
        "partido_id": partido_id,
        "score_local": int(score_local),
        "score_away": int(score_away),
        "winner": calcular_ganador(int(score_local), int(score_away))
    }


# -------------------------
# LÓGICA DE RESULTADOS
# -------------------------
def calcular_ganador(score_local, score_away):
    if score_local > score_away:
        return "Local"
    elif score_away > score_local:
        return "Visitante"
    return "Empate"


# -------------------------
# PUNTAJE POR PREDICCIÓN
# -------------------------
def calcular_puntaje_prediccion(prediccion, resultado):
    """
    Reglas:
    - Ganador correcto: 10 pts
    - Marcador exacto: 40 pts
    """
    puntos = 0

    # Marcador exacto
    if (
        prediccion["score_local"] == resultado["score_local"]
        and prediccion["score_away"] == resultado["score_away"]
    ):
        return 40

    # Ganador correcto
    if prediccion["pick"] == resultado["winner"]:
        puntos += 10

    return puntos


# -------------------------
# CALCULAR PUNTAJES DEL PARTIDO
# -------------------------
def calcular_puntajes_partido(partido_id):
    """
    Calcula puntaje para todos los usuarios en un partido
    """
    resultado = fetch_match_result(partido_id)
    if not resultado:
        return []

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, pick, score_local, score_away
        FROM predicciones
        WHERE partido_id = ?
    """, (partido_id,))

    predicciones = cur.fetchall()
    conn.close()

    resultados = []

    for user_id, pick, s_local, s_away in predicciones:
        pred = {
            "pick": pick,
            "score_local": s_local,
            "score_away": s_away
        }

        puntos = calcular_puntaje_prediccion(pred, resultado)

        resultados.append({
            "user_id": user_id,
            "partido_id": partido_id,
            "puntos": puntos
        })

    return resultados


# -------------------------
# RANKING TOTAL
# -------------------------
def ranking_general():
    """
    Suma puntos de todos los partidos
    """
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, SUM(puntos)
        FROM puntajes
        GROUP BY user_id
        ORDER BY SUM(puntos) DESC
    """)

    ranking = cur.fetchall()
    conn.close()

    return ranking
