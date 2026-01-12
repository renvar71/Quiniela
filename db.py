# db.py
import streamlit as st
from datetime import datetime, timedelta
import hashlib

# WEEK_RULES para sensibilidad a la ronda

WEEK_RULES = {
    160: {
        "title": "Ronda Comodines",
        "multiplier": 1,
        "extra_questions": [
            ("extra_question_1", "pregunta1_resultado"),
            ("extra_question_2", "pregunta2_resultado"),
        ]
    },
    125: {
        "title": "Ronda Divisional",
        "multiplier": 1,
        "extra_questions": [
            ("extra_question_1", "pregunta1_resultado"),
            ("extra_question_2", "pregunta2_resultado"),
            ("extra_question_3", "pregunta3_resultado"),
        ]
    },
    150: {
        "title": "Campeón de Conferencia",
        "multiplier": 1,
        "extra_questions": [
            ("extra_question_1", "pregunta1_resultado"),
            ("extra_question_2", "pregunta2_resultado"),
            ("extra_question_3", "pregunta3_resultado"),
            ("extra_question_4", "pregunta4_resultado"),
        ]
    },
    200: {
        "title": "Super Bowl",
        "multiplier": 2,  # 🔥 DUPLICA PUNTOS
        "extra_questions": [
            ("extra_question_1", "pregunta1_resultado"),
            ("extra_question_2", "pregunta2_resultado"),
            ("extra_question_3", "pregunta3_resultado"),
            ("extra_question_4", "pregunta4_resultado"),
            ("extra_question_5", "pregunta5_resultado"),
            ("extra_question_6", "pregunta6_resultado"),
            ("extra_question_7", "pregunta7_resultado"),
            ("extra_question_8", "pregunta8_resultado"),
            ("extra_question_9", "pregunta9_resultado"),
            ("extra_question_10", "pregunta10_resultado"),
        ]
    }
}

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
# NUEVA FUNCIÓN: Se agregara a practicamente todas las funciones
# -------------------------
def get_supabase():
    """
    Obtiene el cliente Supabase desde la sesión.
    Falla explícitamente si no existe (mejor que errores silenciosos).
    """
    if "supabase" not in st.session_state:
        raise RuntimeError("Supabase client no inicializado en session_state")
    return st.session_state.supabase

# -------------------------
# HASH PASSWORD
# -------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------
# USUARIOS
# -------------------------
def get_user_id(email):
    supabase = get_supabase()
    res = supabase.table("usuarios") \
        .select("id") \
        .eq("email", email) \
        .execute()

    if not res.data:
        return None

    return res.data[0]["id"]


def add_user(nombre, email, password):
    try:
        supabase = get_supabase()
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
    supabase = get_supabase()
    supabase.table("equipos").upsert({
        "team_id": team_id,
        "nombre": nombre,
        "badge_url": badge_url,
        "logo_url": logo_url
    }, on_conflict="team_id").execute()


def get_team_badges():
    supabase = get_supabase()
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
    supabase = get_supabase()
    supabase.table("partidos").upsert(
        partido,
        on_conflict="id_partido"
    ).execute()


def get_partidos(semana=None):
    supabase = get_supabase()
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

# CAMBIO MÍNIMO A SAVE_PREDICCION
def save_prediccion(
    usuario_id,
    id_partido,
    semana,
    fecha_partido,  # se deja por compatibilidad, pero NO se usa
    pick,
    score_local=None,
    score_away=None,
    line_over_under=None,
    extra_question_1=None,
    extra_question_2=None
):
    supabase = get_supabase()

    # 1️⃣ Leer SIEMPRE la fecha real desde partidos
    res = (
        supabase
        .table("partidos")
        .select("fecha")
        .eq("id_partido", id_partido)
        .limit(1)
        .execute()
    )

    # 2️⃣ Tomar la fecha correcta
    fecha_real = res.data[0]["fecha"] if res.data else None

    # (opcional pero recomendable)
    if not fecha_real:
        raise RuntimeError(f"No se encontró fecha para partido {id_partido}")

    # 3️⃣ Guardar predicción usando SOLO la fecha real
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
            "fecha_partido": fecha_real
        },
        on_conflict="usuario_id,id_partido"
    ).execute()


# QUITAR DOBLE UPSERT
def has_prediccion(usuario_id, id_partido):
    supabase = get_supabase()
    res = supabase.table("predicciones") \
        .select("id") \
        .eq("usuario_id", usuario_id) \
        .eq("id_partido", id_partido) \
        .execute()

    return bool(res.data)

# -------------------------
# ESTADO PREDICCIÓN
# -------------------------
# CAMBIOS PARA DESHABILITAR PREDICCION CONSIDERANDO TABLA EN UTC
#from datetime import datetime, timedelta, date
from datetime import datetime, timedelta, timezone

def get_prediccion_status(usuario_id, id_partido, fecha_partido):
    # -------------------------
    # VALIDACIÓN BÁSICA
    # -------------------------
    if not usuario_id or not id_partido:
        return "🟡 Pendiente"

    #cnow = datetime.now()
    now = datetime.now(timezone.utc)

    # -------------------------
    # QUERY SEGURA
    # -------------------------
    supabase = get_supabase()
    res = (
        supabase
        .table("predicciones")
        .select("fecha_partido")
        .eq("usuario_id", usuario_id)
        .eq("id_partido", id_partido)
        .limit(1)
        .execute()
    )
    def _is_expired(dt):
        return now >= dt - timedelta(minutes=1)
    # -------------------------
    # FECHA DESDE DB
    # -------------------------

    if res.data:
        db_fecha = res.data[0].get("fecha_partido")
        if isinstance(db_fecha, str):
            try:
                partido_dt = datetime.fromisoformat(
                    db_fecha.replace("Z", "+00:00")
                ).astimezone(timezone.utc)

                if _is_expired(partido_dt):
                    return "🔴 Expirada"
            except Exception:
                pass
        return "🟢 Registrada"

    # ---------- FECHA DESDE PARTIDOS ----------
    if isinstance(fecha_partido, str):
        try:
            partido_dt = datetime.fromisoformat(
                fecha_partido.replace("Z", "+00:00")
            ).astimezone(timezone.utc)

            if _is_expired(partido_dt):
                return "🔴 Expirada"
        except Exception:
            pass

    return "🟡 Pendiente"


# -------------------------
# PUNTAJES
# -------------------------
def save_puntaje(usuario_id, id_partido, semana, puntos):
    supabase = get_supabase()
    supabase.table("puntajes").upsert({
        "usuario_id": usuario_id,
        "id_partido": id_partido,
        "semana": semana,
        "puntos": puntos
    }, on_conflict="usuario_id,id_partido").execute()

# -------------------------
# RESULTADOS ADMIN (solo lectura)
# -------------------------
def get_resultado_admin(id_partido=None):
    supabase = get_supabase()
    query = supabase.table("resultados_admin").select("*")
    if id_partido is not None:
        query = query.eq("id_partido", id_partido)
    res = query.execute()
    return res.data or []

# -------------------------
# PREDICCION DE USUARIO PARA HABILITAR EL CAMBIO DE PREDICCIÓN
# -------------------------

def get_prediccion_by_user(usuario_id, id_partido):
    supabase = get_supabase()
    res = (
        supabase
        .table("predicciones")
        .select("*")
        .eq("usuario_id", usuario_id)
        .eq("id_partido", id_partido)
        .limit(1)
        .execute()
    )

    if res.data:
        return res.data[0]

    return None
## Definir otra funcion similar
def get_prediccion_by_user_optimized(usuario_id):
    supabase = get_supabase()

    res = (
        supabase
        .table("predicciones")
        .select("*")
        .eq("usuario_id", usuario_id)
        .execute()
    )

    return res.data or []
## Funciones centralizadas para tabla:
def get_usuarios():
    supabase = get_supabase()
    res = supabase.table("usuarios").select("id, nombre").execute()
    return res.data or []


def get_puntajes():
    supabase = get_supabase()
    res = supabase.table("puntajes").select(
        "usuario_id, puntos, semana"
    ).execute()
    return res.data or []

def get_equipos():
    supabase = get_supabase()
    res = (
        supabase
        .table("equipos")
        .select("*")
        .execute()
    )
    return res.data or []

# GET PARTIDOS RESUELTOS
def get_partidos_resueltos():
    """
    Devuelve solo partidos finalizados
    """
    supabase = get_supabase()
    res = (
        supabase
        .table("partidos")
        .select("id_partido, semana")
        .eq("confirmed_result", True)
        .execute()
    )
    return res.data or []


# Ya se calculó?
def existe_partido_en_puntajes(id_partido):
    supabase = get_supabase()
    res = (
        supabase
        .table("puntajes")
        .select("id")
        .eq("partido_id", id_partido)
        .not_.is_("puntos", None)
        .limit(1)
        .execute()
    )
    return bool(res.data)
  
