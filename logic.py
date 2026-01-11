from supabase_config import supabase
from db import WEEK_RULES

# -------------------------
# RESULTADO REAL DEL PARTIDO
# -------------------------

# nombre de equipo:
def get_nombre_equipo(team_id):
    res = (
        supabase
        .table("equipos")
        .select("nombre")
        .eq("team_id", team_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    return res.data[0]["nombre"]

def calcular_ganador_nombre(partido):
    """
    RETORNA EL NOMBRE DEL EQUIPO GANADOR O NONE SI HAY EMPATE
    """
    if partido["score_local"] > partido["score_away"]:
        return get_nombre_equipo(partido["equipo_local_id"])
        
    if partido["score_away"] > partido["score_local"]:
        return get_nombre_equipo(partido["equipo_visitante_id"])
        
    return None # Empate

def get_resultado_partido(id_partido):
    res = (
        supabase
        .table("partidos")
        .select(
            "score_local, score_away, status, equipo_local_id, equipo_visitante_id"
        )
        .eq("id_partido", id_partido)
        .limit(1)
        .execute()
    )

    if not res.data:
        return None

    p = res.data[0]

    if p["status"] != "finished":
        return None

    if p["score_local"] is None or p["score_away"] is None:
        return None

    ganador_nombre = calcular_ganador_nombre(p) # Cambio 1

    return {
        "score_local": p["score_local"],
        "score_away": p["score_away"],
        "winner_name": ganador_nombre
        # "equipo_local_id": p["equipo_local_id"],
        # "equipo_visitante_id": p["equipo_visitante_id"],
    }
# -------------------------
# RESULTADO ADMIN
# -------------------------
def get_resultado_admin_partido(id_partido):
    res = (
        supabase
        .table("resultados_admin")
        .select("*")
        .eq("id_partido", id_partido)
        .limit(1)
        .execute()
    )

    if not res.data:
        return None

    return res.data[0]


# -------------------------
# PUNTAJE BASE
# -------------------------
def calcular_puntaje_prediccion(pred, resultado): # Cambio 2
    """
    Reglas:
    - Marcador exacto: 40 pts
    - Ganador correcto: 10 pts
    """
    # 🎯 Marcador exacto
    if (
        pred["score_local"] == resultado["score_local"]
        and pred["score_away"] == resultado["score_away"]
    ):
        return 40

    # 🏆 Ganador correcto (por team_id)
    # winner_team_id = admin.get("winner_team_id")

    # if winner_team_id and pred["pick"] == winner_team_id:
    #     return 10
    if resultado["winner_name"] and pred["pick"] == resultado["winner_name"]:
        return 10

    return 0

# -------------------------
# PUNTOS EXTRA
# -------------------------
def calcular_puntos_extras(pred, admin, semana):
    rules = WEEK_RULES.get(semana)
    if not rules:
        return 0

    puntos = 0

    for pred_col, admin_col in rules["extra_questions"]:
        valor_real = admin.get(admin_col)

        if valor_real is None:
            continue

        # Empate → todos ganan
        if valor_real == "Empate":
            puntos += 3
            continue

        valor_pred = pred.get(pred_col)

        if valor_pred == valor_real:
            puntos += 3

    return puntos


# -------------------------
# OVER / UNDER
# -------------------------
def puntos_over_under(pred, o_u_real):
    if o_u_real and pred.get("line_over_under") == o_u_real:
        return 8
    return 0


# -------------------------
# CALCULAR PUNTAJES DEL PARTIDO
# -------------------------
def calcular_puntajes_partido(id_partido, semana):
    resultado = get_resultado_partido(id_partido)
    if not resultado:
        return []

    admin = get_resultado_admin_partido(id_partido)
    if not admin:
        return []

    rules = WEEK_RULES.get(semana, {"multiplier": 1})
    multiplier = rules["multiplier"]

    preds = (
        supabase
        .table("predicciones")
        .select("*")
        .eq("id_partido", id_partido)
        .execute()
    ).data or []

    resultados = []

    for p in preds:
        puntos_base = calcular_puntaje_prediccion(p, resultado) # Cambio 3
        puntos_ou = puntos_over_under(p, admin.get("o_u_resultado"))
        puntos_extra = calcular_puntos_extras(p, admin, semana)

        puntos_totales = (puntos_base + puntos_ou + puntos_extra) * multiplier

        supabase.table("puntajes").upsert(
            {
                "usuario_id": p["usuario_id"],
                "partido_id": id_partido,
                "semana": semana,
                "puntos": puntos_totales,
            },
            on_conflict="usuario_id,partido_id",
        ).execute()

        resultados.append(
            {
                "usuario_id": p["usuario_id"],
                "id_partido": id_partido,
                "puntos": puntos_totales,
            }
        )

    return resultados
