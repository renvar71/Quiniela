# db.py
from supabase_config import supabase
from datetime import datetime, timedelta
import hashlib

WEEK_TITLES = {
    160: "Próximos partidos Ronda Comodines",
    125: "Próximos partidos Ronda Divisional",
    150: "Próximos partidos Campeón de Conferencia",
    200: "Próximo partido Super Bowl",
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------------------
# Usuarios
# ----------------------------
def get_user_id(email):
    res = supabase.table("usuarios").select("id").eq("email", email).single().execute()
    return res.data["id"] if res.data else None

# ----------------------------
# Partidos
# ----------------------------
def get_partidos(semana=None):
    query = supabase.table("partidos").select("*").order("fecha", desc=False)
    if semana is not None:
        query = query.eq("semana", semana)
    res = query.execute()
    return res.data

# ----------------------------
# Predicciones
# ----------------------------
def save_prediccion(user_id, partido_id, semana, fecha_del_partido,
                    pick, score_local=None, score_away=None,
                    line_over_under=None, extra_question=None):
    supabase.table("predicciones").insert({
        "usuario_id": user_id,
        "partido_id": partido_id,
        "semana": semana,
        "pick": pick,
        "score_local": score_local,
        "score_away": score_away,
        "line_over_under": line_over_under,
        "extra_question": extra_question,
        "fecha_partido": fecha_del_partido
    }).execute()

def has_prediccion(usuario_id, partido_id):
    res = supabase.table("predicciones")\
        .select("id")\
        .eq("usuario_id", usuario_id)\
        .eq("partido_id", partido_id)\
        .execute()
    return len(res.data) > 0

def get_prediccion_status(user_id, partido_id, fecha_partido):
    # Checar si existe predicción
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

# ----------------------------
# Puntajes
# ----------------------------
def save_puntaje(usuario_id, partido_id, semana, puntos):
    # Insert or update (upsert)
    supabase.table("puntajes").upsert([{
        "usuario_id": usuario_id,
        "partido_id": partido_id,
        "semana": semana,
        "puntos": puntos
    }], on_conflict=["usuario_id", "partido_id"]).execute()
