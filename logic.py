from supabase_config import supabase
from db import WEEK_RULES

# -------------------------
# RESULTADO REAL DEL PARTIDO
# -------------------------

def get_resultado_partido(id_partido):
    res = (
        supabase
        .table("partidos")
        .select(
            "score_local, score_away, status, home_team, away_team"
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

    # Determinar ganador REAL (nombre del equipo)
    if p["score_local"] > p["score_away"]:
        winner_team = p["home_team"]
    elif p["score_away"] > p["score_local"]:
        winner_team = p["away_team"]
    else:
        winner_team = "Empate"

    return {
        "score_local": p["score_local"],
        "score_away": p["score_away"],
        "winner_team": winner_team
    }


# -------------------------
# PUNTAJE POR PREDICCIÓN
# -------------------------

def calcular_puntaje_prediccion(pred, resultado):
    """
    Reglas:
    - Marcador exacto: 40 pts
    - Ganador correcto: 10 pts
    """
    # Marcador exacto
    if (
        pred["score_local"] == resultado["score_local"]
        and pred["score_away"] == resultado["score_away"]
    ):
        return 40

    # Ganador correcto (comparando nombres de equipo)
    if (
        resultado["winner_team"] != "Empate"
        and pred["pick"] == resultado["winner_team"]
    ):
        return 10

    return 0


# -------------------------
# PREGUNTAS EXTRA
# -------------------------

def calcular_puntos_extras(pred, admin, semana):
    rules = WEEK_RULES.get(semana)
    if not rules:
        return 0

    puntos = 0

    for pred_col, admin_col in rules["extra_questions"]:
        valor_real = admin.get(admin_col)

        # Pregunta no activa
        if valor_real is None:
            continue

        # Empate → todos ganan puntos
        if valor_real == "Empate":
            puntos += 3
            continue

        valor_pred = pred.get(pred_col)

        if valor_pred is None:
            continue

        if valor_pred == valor_real:
            puntos += 3

    return puntos


# -------------------------
# OVER / UNDER
# -------------------------

def puntos_over_under(pred, o_u_resultado):
    if o_u_resultado and pred.get("line_over_under") == o_u_resultado:
        return 8
    return 0


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
# FUNCIÓN PRINCIPAL
# -------------------------

def calcular_puntajes_partido(id_partido, semana):
    resultado = get_resultado_partido(id_partido)
    if not resultado:
        return []

    admin = get_resultado_admin_partido(id_partido)

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
        puntos_base = calcular_puntaje_prediccion(p, resultado)

        puntos_ou = 0
        puntos_extra = 0

        if admin:
            puntos_ou = puntos_over_under(p, admin.get("o_u_resultado"))
            puntos_extra = calcular_puntos_extras(p, admin, semana)

        puntos_totales = (puntos_base + puntos_ou + puntos_extra) * multiplier

        supabase.table("puntajes").upsert(
            {
                "usuario_id": p["usuario_id"],
                "partido_id": id_partido,
                "semana": semana,
                "puntos": puntos_totales
            },
            on_conflict="usuario_id,partido_id"
        ).execute()

        resultados.append({
            "usuario_id": p["usuario_id"],
            "partido_id": id_partido,
            "puntos": puntos_totales
        })

    return resultados
