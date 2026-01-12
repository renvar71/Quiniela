# jugadores.py
import streamlit as st
import pandas as pd
from supabase_config import supabase
from db import WEEK_TITLES

# -------------------------
# SESSION CHECK
# -------------------------
if not st.session_state.get("logged_in"):
    st.warning("Debes iniciar sesión")
    st.stop()

user_id = st.session_state.get("user_id")
if not user_id:
    st.stop()

st.title("👥 Comparar Predicciones")

# -------------------------
# SELECT SEMANA
# -------------------------
semanas_resp = (
    supabase
    .table("partidos")
    .select("semana")
    .order("semana")
    .execute()
)

semanas = sorted({r["semana"] for r in semanas_resp.data})

semana_labels = {
    s: WEEK_TITLES.get(s, f"Semana {s}")
    for s in semanas
}

semana_label = st.selectbox(
    "Semana",
    options=[None] + list(semana_labels.values())
)

if not semana_label:
    st.stop()

semana = next(k for k, v in semana_labels.items() if v == semana_label)

# -------------------------
# SELECT PARTIDO (FINALIZADOS)
# -------------------------
partidos_resp = (
    supabase
    .table("partidos")
    .select("id_partido, equipo_local_id, equipo_visitante_id, status")
    .eq("semana", semana)
    .eq("status", "finished")
    .execute()
)

if not partidos_resp.data:
    st.warning("No hay partidos finalizados")
    st.stop()

partidos_df = pd.DataFrame(partidos_resp.data)

# -------------------------
# FETCH PUNTAJE
# -------------------------
puntaje_resp = (
    supabase
    .table("puntaje")
    .select("usuario_id, id_partido, puntos")
    .eq("id_partido", partido_id)
    .execute()
)

puntaje_df = pd.DataFrame(puntaje_resp.data) if puntaje_resp.data else pd.DataFrame(
    columns=["usuario_id", "id_partido", "puntos"]
)

# -------------------------
# RESOLVER EQUIPOS
# -------------------------
equipo_ids = list(set(
    partidos_df["equipo_local_id"].tolist()
    + partidos_df["equipo_visitante_id"].tolist()
))

equipos_resp = (
    supabase
    .table("equipos")
    .select("team_id, nombre")
    .in_("team_id", equipo_ids)
    .execute()
)

equipos_map = {e["team_id"]: e["nombre"] for e in equipos_resp.data}

partidos_df["label"] = partidos_df.apply(
    lambda r: f"{equipos_map.get(r['equipo_local_id'], '—')} vs {equipos_map.get(r['equipo_visitante_id'], '—')}",
    axis=1
)

partido_label = st.selectbox(
    "Partido",
    options=[None] + partidos_df["label"].tolist()
)

if not partido_label:
    st.stop()

partido_id = partidos_df.loc[
    partidos_df["label"] == partido_label, "id_partido"
].iloc[0]

# -------------------------
# FETCH PREDICCIONES
# -------------------------
pred_resp = (
    supabase
    .table("predicciones")
    .select("usuario_id, score_local, score_away, pick, line_over_under, extra_question_1, extra_question_2")
    .eq("id_partido", partido_id)
    .execute()
)

if not pred_resp.data:
    st.warning("No hay predicciones")
    st.stop()

pred_df = pd.DataFrame(pred_resp.data)

pred_df = pred_df.merge(
    puntaje_df[["usuario_id", "puntos"]],
    on="usuario_id",
    how="left"
)

pred_df["puntos"] = pred_df["puntos"].fillna(0)


# -------------------------
# RESOLVER USUARIOS
# -------------------------
user_ids = pred_df["usuario_id"].unique().tolist()

users_resp = (
    supabase
    .table("usuarios")
    .select("id, nombre")
    .in_("id", user_ids)
    .execute()
)

user_map = {u["id"]: u["nombre"] for u in users_resp.data}

pred_df["username"] = pred_df["usuario_id"].map(user_map)

# -------------------------
# FORMATEAR DF
# -------------------------
df = pred_df.rename(columns={
    "score_local": "Marcador Local",
    "score_away": "Marcador Visitante",
    "pick": "Ganador",
    "line_over_under": "Linea",
    "extra_question_1": "Pregunta Extra 1",
    "extra_question_2": "Pregunta Extra 2",
    "puntos": "Puntos"
})

# -------------------------
# FILTRO JUGADORES
# -------------------------
jugadores = df["username"].dropna().unique().tolist()

default_user = [user_map[user_id]] if user_id in user_map else []

seleccionados = st.multiselect(
    "Comparar con jugadores",
    jugadores,
    default=default_user
)


df = df[df["username"].isin(seleccionados)]


# -------------------------
# ORDEN (PUNTOS DESC, YO DESTACADO)
# -------------------------
df = df.sort_values(
    by=["Puntos"],
    ascending=False
)

# -------------------------
# STYLER (FIX DEFINITIVO)
# -------------------------
def highlight_user(row):
    if row["usuario_id"] == user_id:
        return ["background-color: #1f77b4; color: white"] * len(row)
    return [""] * len(row)

styled_df = (
    df[[
        "username",
        "Puntos",
        "Marcador Local",
        "Marcador Visitante",
        "Ganador",
        "Linea",
        "Pregunta Extra 1",
        "Pregunta Extra 2"
    ]]
    .style
    .apply(
        lambda row: ["background-color: #1f77b4; color: white"] * len(row)
        if df.loc[row.name, "usuario_id"] == user_id
        else ["" for _ in row],
        axis=1
    )
)

st.caption(f"Comparando {len(df)} predicciones")

st.dataframe(
    styled_df,
    use_container_width=True
)
