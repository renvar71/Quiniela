import requests
from supabase_config import supabase
from api import API_KEY

# -------------------------
# RESULTADO REAL DEL PARTIDO
# -------------------------
# def fetch_match_result(partido_id):
#     """
#     Obtiene marcador final desde TheSportsDB
#     """
#     url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookupevent.php?id={partido_id}"
#     r = requests.get(url, timeout=10)
#     r.raise_for_status()

#     data = r.json().get("events", [])
#     if not data:
#         return None

#     e = data[0]

#     score_local = e.get("intHomeScore")
#     score_away = e.get("intAwayScore")

#     if score_local is None or score_away is None:
#         return None  # partido no finalizado

#     return {
#         "partido_id": partido_id,
#         "score_local": int(score_local),
#         "score_away": int(score_away),
#         "winner": calcular_ganador(int(score_local), int(score_away))
#     }

# Extraemos de supabase sin llamar a la API para que sea rápido y extraemos finished para que si es FALSE no se haga el cálculo
def get_resultado_partido(id_partido):
    res = (
        supabase
        .table("partidos")
        .select("score_local, score_away, finished")
        .eq("id_partido", id_partido)
        .limit(1)
        .execute()
    )

    if not res.data:
        return None

    p = res.data[0]

    if not p["finished"]:
        return None

    return {
        "score_local": p["score_local"],
        "score_away": p["score_away"],
        "winner": calcular_ganador(p["score_local"], p["score_away"])
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

def puntos_preguntas_extra(pred, extra_1_ok, extra_2_ok):
    puntos = 0

    if extra_1_ok and pred.get("extra_question_1") == extra_1_ok:
        puntos += 5

    if extra_2_ok and pred.get("extra_question_2") == extra_2_ok:
        puntos += 5
        
    # VALIDACION DE EMPATE
    
    if extra_1_ok == "Empate":
        puntos += 5
        
    if extra_2_ok == "Empate":
        puntos += 5
        
    return puntos

def puntos_over_under(pred, o_u):
    puntos = 0
    if o_u and pred.get("line_over_under") == o_u:
        puntos += 8
    return puntos

# -------------------------
# CALCULAR PUNTAJES DEL PARTIDO FUNCION A LLAMAR, GUARDA EN SUPABASE Y REGRESA LISTA RESULTADOS
# -------------------------
def calcular_puntajes_partido(id_partido, semana):
    resultado = get_resultado_partido(id_partido)
    if not resultado:
        return []
    admin = get_resultado_admin_partido(id_partido)
    if not admin:
        return []
        
    o_u = admin.get("o_u_resultado")
    extra_1_correcta = admin.get("pregunta1_resultado")
    extra_2_correcta = admin.get("pregunta2_resultado")
    
    if o_u is None or extra_1_correcta is None or extra_2_correcta is None:
        return []
        
    preds = (
        supabase
        .table("predicciones")
        .select("usuario_id, pick, score_local, score_away, line_over_under, extra_question_1, extra_question_2")
        .eq("id_partido", id_partido)
        .execute()
    ).data or []

    resultados = []
    
    for p in preds:
        puntos = (
            calcular_puntaje_prediccion(p, resultado) 
            + puntos_over_under(p, o_u) 
            + puntos_preguntas_extra(p, extra_1_correcta, extra_2_correcta)
        )
##nDUDA
        # 🔥 Guardar directamente en Supabase
        supabase.table("puntajes").upsert(
            {
                "usuario_id": p["usuario_id"],
                "partido_id": id_partido,
                "semana": semana,
                "puntos": puntos
            },
            on_conflict="usuario_id,partido_id"
        ).execute()

        resultados.append({
            "usuario_id": p["usuario_id"],
            "id_partido": id_partido,
            "puntos": puntos
        })

    return resultados

# -------------------------
# RANKING TOTAL
# -------------------------
def ranking_general():
    res = (
        supabase
        .table("puntajes")
        .select("usuario_id, puntos")
        .execute()
    )

    ranking = {}
    for r in res.data or []:
        ranking[r["usuario_id"]] = ranking.get(r["usuario_id"], 0) + r["puntos"]

    return sorted(
        ranking.items(),
        key=lambda x: x[1],
        reverse=True
    )
def get_resultado_admin_partido(id_partido):
    res = (
        supabase
        .table("resultados_admin")
        .select("o_u_resultado, pregunta1_resultado, pregunta2_resultado")
        .eq("id_partido", id_partido)
        .limit(1)
        .execute()
    )

    if not res.data:
        return None

    return res.data[0]
