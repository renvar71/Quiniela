from supabase_config import supabase
from datetime import datetime, timedelta
import hashlib

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
        on_conflict="partido_id"
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
    partido_id,
    semana,
    fecha_partido,
    pick,
    score_local=None,
    score_away=None,
    line_over_under=None,
    extra_question=None
):
    supabase.table("predicciones").upsert({
        "usuario_id": usuario_id,
        "partido_id": partido_id,
        "semana": semana,
        "pick": pick,
        "score_local": score_local,
        "score_away": score_away,
        "line_over_under": line_over_under,
        "extra_question": extra_question,
        "fecha_partido": fecha_partido
    }, on_conflict="usuario_id,partido_id").execute()


def has_prediccion(usuario_id, partido_id):
    res = supabase.table("predicciones") \
        .select("id") \
        .eq("usuario_id", usuario_id) \
        .eq("partido_id", partido_id) \
        .execute()

    return bool(res.data)

# -------------------------
# ESTADO PREDICCIÓN
# -------------------------
def get_prediccion_status(usuario_id, partido_id, fecha_partido):
    res = supabase.table("predicciones") \
        .select("fecha_partido") \
        .eq("usuario_id", usuario_id) \
        .eq("partido_id", partido_id) \
        .execute()

    now = datetime.now()

    if res.data:
        db_fecha = res.data[0].get("fecha_partido")
        if db_fecha:
            try:
                partido_dt = datetime.fromisoformat(db_fecha)
                if now >= partido_dt - timedelta(minutes=1):
                    return "🔴 Expirada"
            except ValueError:
                pass
        return "🟢 Registrada"

    if fecha_partido:
        try:
            partido_dt = datetime.fromisoformat(fecha_partido)
            if now >= partido_dt - timedelta(minutes=1):
                return "🔴 Expirada"
        except ValueError:
            pass

    return "🟡 Pendiente"

# -------------------------
# PUNTAJES
# -------------------------
def save_puntaje(usuario_id, partido_id, semana, puntos):
    supabase.table("puntajes").upsert({
        "usuario_id": usuario_id,
        "partido_id": partido_id,
        "semana": semana,
        "puntos": puntos
    }, on_conflict="usuario_id,partido_id").execute()
