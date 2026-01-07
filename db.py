from datetime import datetime, timedelta, date
import hashlib
import time
import httpx
from supabase import create_client
from supabase_config import SUPABASE_URL, SUPABASE_KEY

# -------------------------
# SUPABASE CLIENT
# -------------------------
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# RETRY CONTROLADO
# -------------------------
def execute_with_retry(query, retries=3, delay=0.3):
    for attempt in range(retries):
        try:
            return query.execute()
        except (
            httpx.ReadError,
            httpx.ConnectError,
            httpx.RemoteProtocolError,
            httpx.TimeoutException,
        ):
            if attempt == retries - 1:
                raise
            time.sleep(delay)

# -------------------------
# TITULOS POR SEMANA
# -------------------------
WEEK_TITLES = {
    160: "Ronda Comodines",
    125: "Ronda Divisional",
    150: "Campeón de Conferencia",
    200: "Super Bowl",
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
    sb = get_supabase()
    res = execute_with_retry(
        sb.table("usuarios")
        .select("id")
        .eq("email", email)
        .limit(1)
    )
    return res.data[0]["id"] if res.data else None


def add_user(nombre, email, password):
    sb = get_supabase()
    try:
        execute_with_retry(
            sb.table("usuarios").insert({
                "nombre": nombre,
                "email": email,
                "password_hash": hash_password(password)
            })
        )
        return True
    except Exception:
        return False

# -------------------------
# EQUIPOS
# -------------------------
def save_team(team_id, nombre, badge_url=None, logo_url=None):
    sb = get_supabase()
    execute_with_retry(
        sb.table("equipos").upsert(
            {
                "team_id": team_id,
                "nombre": nombre,
                "badge_url": badge_url,
                "logo_url": logo_url
            },
            on_conflict="team_id"
        )
    )


def get_team_badges():
    sb = get_supabase()
    res = execute_with_retry(
        sb.table("equipos").select("team_id, badge_url")
    )
    return {t["team_id"]: t["badge_url"] for t in res.data} if res.data else {}

# -------------------------
# PARTIDOS
# -------------------------
def save_partido(partido: dict):
    sb = get_supabase()
    execute_with_retry(
        sb.table("partidos").upsert(partido, on_conflict="id_partido")
    )


def get_partidos(semana=None):
    sb = get_supabase()
    query = sb.table("partidos").select("*").order("fecha", desc=False)
    if semana is not None:
        query = query.eq("semana", semana)
    res = execute_with_retry(query)
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
    sb = get_supabase()
    execute_with_retry(
        sb.table("predicciones").upsert(
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
        )
    )


def has_prediccion(usuario_id, id_partido):
    sb = get_supabase()
    res = execute_with_retry(
        sb.table("predicciones")
        .select("id")
        .eq("usuario_id", usuario_id)
        .eq("id_partido", id_partido)
        .limit(1)
    )
    return bool(res.data)

# -------------------------
# ESTADO PREDICCIÓN
# -------------------------
def get_prediccion_status(usuario_id, id_partido, fecha_partido):
    if not usuario_id or not id_partido:
        return "🟡 Pendiente"

    sb = get_supabase()
    now = datetime.now()

    res = execute_with_retry(
        sb.table("predicciones")
        .select("fecha_partido")
        .eq("usuario_id", usuario_id)
        .eq("id_partido", id_partido)
        .limit(1)
    )

    if res.data:
        db_fecha = res.data[0].get("fecha_partido")
        try:
            partido_dt = datetime.fromisoformat(db_fecha.replace("Z", ""))
            if now >= partido_dt - timedelta(minutes=1):
                return "🔴 Expirada"
        except Exception:
            pass
        return "🟢 Registrada"

    try:
        if isinstance(fecha_partido, str):
            partido_dt = datetime.fromisoformat(fecha_partido.replace("Z", ""))
        elif isinstance(fecha_partido, datetime):
            partido_dt = fecha_partido
        elif isinstance(fecha_partido, date):
            partido_dt = datetime.combine(fecha_partido, datetime.min.time())
        else:
            return "🟡 Pendiente"

        if now >= partido_dt - timedelta(minutes=1):
            return "🔴 Expirada"
    except Exception:
        pass

    return "🟡 Pendiente"

# -------------------------
# PUNTAJES
# -------------------------
def save_puntaje(usuario_id, id_partido, semana, puntos):
    sb = get_supabase()
    execute_with_retry(
        sb.table("puntajes").upsert(
            {
                "usuario_id": usuario_id,
                "id_partido": id_partido,
                "semana": semana,
                "puntos": puntos
            },
            on_conflict="usuario_id,id_partido"
        )
    )

# -------------------------
# RESULTADOS ADMIN
# -------------------------
def get_resultado_admin(id_partido=None):
    sb = get_supabase()
    query = sb.table("resultados_admin").select("*")
    if id_partido is not None:
        query = query.eq("id_partido", id_partido)
    res = execute_with_retry(query)
    return res.data or []
