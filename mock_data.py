# mock_data.py

import requests
from api import API_KEY

def get_mock_match(partido_id):
    """
    En TEST MODE usamos la API real,
    pero SOLO para partidos históricos
    """
    url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookupevent.php?id={partido_id}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()

    data = r.json().get("events", [])
    if not data:
        return None

    e = data[0]

    return {
        "partido_id": partido_id,
        "score_local": int(e["intHomeScore"]),
        "score_away": int(e["intAwayScore"]),
        "winner": calcular_ganador(
            int(e["intHomeScore"]),
            int(e["intAwayScore"])
        )
    }
