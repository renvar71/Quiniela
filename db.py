from supabase_config import supabase
from datetime import datetime, timedelta
import hashlib

# -------------------------
# TITULOS POR SEMANA
# -------------------------
WEEK_TITLES = {
    160: "Próximos partidos Ronda Comodines",
    125: "Próximos partidos Ronda Divisional",
    150: "Próximos partidos Campeón de Conferencia",
    200: "Próximo partido Super Bowl",
}


# -------------------------
# HASH PASSWORD
# -------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------
# USUARIOS
# -------------------------
def get_user_id(email):
    res = supabase.table("usuarios") \
        .select("id") \
        .eq("email", email) \
        .execute()

    if not res.data:
        return None

    return res.data[0]["id"]


def add_user(nombre, email, password):
    try:
        supabase.table("usuarios").insert({
            "nombre": nombre,
            "email": email,
            "password_hash": hash_password(password)
        }).execute()
        return True
    except Exception:
        return False

# -------------------------
# EQUIPOS
# -------------------------
def save_team(team_id, nombre, badge_url=None, logo_url=None):
    supabase.table("equipos").upsert({
        "team_id": team_id,
        "nombre": nombre,
        "badge_url": badge_url,
        "logo_url": logo_url
    }, on_conflict="team_id").execute()


def get_team_badges():
    res = supabase.table("equipos") \
        .select("team_id, badge_url") \
        .execute()

    if not res.data:
        return {}

    return {t["team_id"]: t["badge_url"] for t in res.data}

# -------------------------
# PARTIDOS
# -------------------------
def save_partido(partido: dict):
    supabase.table("partidos").upsert(
        partido,
        on_conflict="id_partido"
    ).execute()


def get_partidos(semana=None):
    query = supabase.table("partidos") \
        .select("*") \
        .order("fecha", desc=False)

    if semana is not None:
        query = query.eq("semana", semana)

    res = query.execute()
    return res.data or []


# -------------------------
# PREDICCIONES
# -------------------------
def save_prediccion(
    usuario_id,
    id_partido,
    semana,
    fecha_partido,
    pick,
    score_local=None,
    score_away=None,
    line_over_under=None,
    extra_question_1=None,
    extra_question_2=None
):
    supabase.table("predicciones").upsert(
        {
            "usuario_id": usuario_id,
            "id_partido": id_partido,
            "semana": semana,
            "pick": pick,
            "score_local": score_local,
            "score_away": score_away,
            "line_over_under": line_over_under,
            "extra_question_1": extra_question_1,
            "extra_question_2": extra_question_2,
            "fecha_partido": fecha_partido
        },
        on_conflict="usuario_id,id_partido"
    ).execute()

    supabase.table("predicciones").upsert(
        {
            "usuario_id": usuario_id,
            "id_partido": id_partido,
            "semana": semana,
            "pick": pick,
            "score_local": score_local,
            "score_away": score_away,
            "line_over_under": line_over_under,
            "extra_question_1": extra_question_1,
            "extra_question_2": extra_question_2,
            "fecha_partido": fecha_partido
        },
        on_conflict="usuario_id,id_partido"
    ).execute()


def has_prediccion(usuario_id, id_partido):
    res = supabase.table("predicciones") \
        .select("id") \
        .eq("usuario_id", usuario_id) \
        .eq("id_partido", id_partido) \
        .execute()

    return bool(res.data)

# -------------------------
# ESTADO PREDICCIÓN
# -------------------------
from datetime import datetime, timedelta, date

def get_prediccion_status(usuario_id, id_partido, fecha_partido):
    # -------------------------
    # VALIDACIÓN BÁSICA
    # -------------------------
    if not usuario_id or not id_partido:
        return "🟡 Pendiente"

    now = datetime.now()

    # -------------------------
    # QUERY SEGURA
    # -------------------------
    res = (
        supabase
        .table("predicciones")
        .select("fecha_partido")
        .eq("usuario_id", usuario_id)
        .eq("id_partido", id_partido)
        .limit(1)
        .execute()
    )

    # -------------------------
    # FECHA DESDE DB
    # -------------------------
    if res.data:
        db_fecha = res.data[0].get("fecha_partido")
        if isinstance(db_fecha, str):
            try:
                partido_dt = datetime.fromisoformat(db_fecha.replace("Z", ""))
                if now >= partido_dt - timedelta(minutes=1):
                    return "🔴 Expirada"
            except Exception:
                pass
        return "🟢 Registrada"

    # -------------------------
    # FECHA DESDE CONTEXTO
    # -------------------------
    if isinstance(fecha_partido, (datetime, date)):
        partido_dt = (
            fecha_partido
            if isinstance(fecha_partido, datetime)
            else datetime.combine(fecha_partido, datetime.min.time())
        )
        if now >= partido_dt - timedelta(minutes=1):
            return "🔴 Expirada"

    if isinstance(fecha_partido, str):
        try:
            partido_dt = datetime.fromisoformat(fecha_partido.replace("Z", ""))
            if now >= partido_dt - timedelta(minutes=1):
                return "🔴 Expirada"
        except Exception:
            pass

    return "🟡 Pendiente"


# -------------------------
# PUNTAJES
# -------------------------
def save_puntaje(usuario_id, id_partido, semana, puntos):
    supabase.table("puntajes").upsert({
        "usuario_id": usuario_id,
        "id_partido": id_partido,
        "semana": semana,
        "puntos": puntos
    }, on_conflict="usuario_id,id_partido").execute()
