# db.py
from supabase_config import supabase
from datetime import datetime, timedelta
import hashlib

# -------------------------
# CONSTANTES
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
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------
# USUARIOS
# -------------------------
def get_user_id(email):
    res = supabase.table("usuarios").select("id").eq("email", email).single().execute()
    return res.data["id"] if res.data else None

def add_user(nombre, email, password):
    try:
        supabase.table("usuarios").insert([{
            "nombre": nombre,
            "email": email,
            "password_hash": hash_password(password)
        }]).execute()
        return True
    except Exception:
        return False

# -------------------------
# EQUIPOS
# -------------------------
def save_team(team_id, nombre, badge_url=None, logo_url=None):
    """Upsert de un equipo"""
    supabase.table("equipos").upsert([{
        "team_id": team_id,
        "nombre": nombre,
        "badge_url": badge_url,
        "logo_url": logo_url
    }], on_conflict=["team_id"]).execute()

def get_team_badges():
    """Devuelve un diccionario {team_id: badge_url}"""
    res = supabase.table("equipos").select("team_id, badge_url").execute()
    return {t["team_id"]: t["badge_url"] for t in res.data}

# -------------------------
# PARTIDOS
# -------------------------
def save_partido(partido):
    """Upsert de un partido (dict con campos del partido)"""
    supabase.table("partidos").upsert([partido], on_conflict=["partido_id"]).execute()

def get_partidos(semana=None):
    query = supabase.table("partidos").select("*").order("fecha", desc=False)
    if semana is not None:
        query = query.eq("semana", semana)
    res = query.execute()
    return res.data

# -------------------------
# PREDICCIONES
# -------------------------
def save_prediccion(user_id, partido_id, semana, fecha_del_partido,
                    pick, score_local=None, score_away=None,
                    line_over_under=None, extra_question=None):
    supabase.table("predicciones").upsert([{
        "usuario_id": user_id,
        "partido_id": partido_id,
        "semana": semana,
        "pick": pick,
        "score_local": score_local,
        "score_away": score_away,
        "line_over_under": line_over_under,
        "extra_question": extra_question,
        "fecha_partido": fecha_del_partido
    }], on_conflict=["usuario_id", "partido_id"]).execute()

def has_prediccion(usuario_id, partido_id):
    res = supabase.table("predicciones")\
        .select("id")\
        .eq("usuario_id", usuario_id)\
        .eq("partido_id", partido_id)\
        .execute()
    return len(res.data) > 0

def get_prediccion_status(user_id, partido_id, fecha_partido):
    """Devuelve 🟢 Registrada, 🟡 Pendiente o 🔴 Expirada"""
    res = supabase.table("predicciones")\
        .select("fecha_partido")\
        .eq("usuario_id", user_id)\
        .eq("partido_id", partido_id)\
        .single().execute()

    if res.data:
        db_fecha = res.data["fecha_partido"]
        if db_fecha:
            try:
                partido_dt = datetime.fromisoformat(db_fecha)
                if datetime.now() >= partido_dt - timedelta(minutes=1):
                    return "🔴 Expirada"
                else:
                    return "🟢 Registrada"
            except ValueError:
                return "🟢 Registrada"
        return "🟢 Registrada"

    # si no hay registro
    if fecha_partido:
        try:
            partido_dt = datetime.fromisoformat(fecha_partido)
            if datetime.now() >= partido_dt - timedelta(minutes=1):
                return "🔴 Expirada"
        except ValueError:
            pass

    return "🟡 Pendiente"

# -------------------------
# PUNTAJES
# -------------------------
def save_puntaje(usuario_id, partido_id, semana, puntos):
    """Upsert puntaje"""
    supabase.table("puntajes").upsert([{
        "usuario_id": usuario_id,
        "partido_id": partido_id,
        "semana": semana,
        "puntos": puntos
    }], on_conflict=["usuario_id", "partido_id"]).execute()
