# jugadores.py
import streamlit as st
import pandas as pd
from supabase_config import supabase
from db import WEEK_TITLES  # asumo que ya existe

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
# SELECT SEMANA (con diccionario)
# -------------------------
semanas_resp = (
    supabase
    .table("partidos")
    .select("semana")
    .order("semana")
    .execute()
)

semanas = sorted({row["semana"] for row in semanas_resp.data})

semana_labels = {
    s: WEEK_TITLES.get(s, f"Semana {s}")
    for s in semanas
}

semana_label = st.selectbox(
    "Semana",
    options=[None] + list(semana_labels.values())
)

if not semana_label:
    st.info("Selecciona una semana para continuar")
    st.stop()

# recuperar número de semana
semana = next(
    k for k, v in semana_labels.items()
    if v == semana_label
)

# -------------------------
# SELECT PARTIDO (SOLO FINALIZADOS)
# -------------------------
partidos_resp = (
    supabase
    .table("partidos")
    .select("id_partido, equipo_local_id, equipo_visitante_id, status")
    .eq("semana", semana)
    .eq("status", "finished")
    .execute()
)

partidos_df = pd.DataFrame(partidos_resp.data)

if partidos_df.empty:
    st.warning("No hay partidos finalizados para esta semana")
    st.stop()

# -------------------------
# RESOLVER NOMBRES DE EQUIPOS
# -------------------------
equipo_ids = set(
    partidos_df["equipo_local_id"].tolist() +
    partidos_df["equipo_visitante_id"].tolist()
)

equipos_resp = (
    supabase
    .table("equipos")
    .select("team_id, nombre")
    .in_("team_id", list(equipo_ids))
    .execute()
)

equipos_map = {
    e["team_id"]: e["nombre"]
    for e in equipos_resp.data
}

partidos_df["label"] = partidos_df.apply(
    lambda r: (
        f"{equipos_map.get(r['equipo_local_id'], '—')} "
        f"vs "
        f"{equipos_map.get(r['equipo_visitante_id'], '—')}"
    ),
    axis=1
)

# -------------------------
# SELECT PARTIDO
# -------------------------
partido_label = st.selectbox(
    "Partido",
    options=[None] + partidos_df["label"].tolist()
)

if not partido_label:
    st.info("Selecciona un partido finalizado")
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
    .select("usuario_id, home_score, away_score, winner")
    .eq("match_id", partido_id)
    .execute()
)

if not pred_resp.data:
    st.warning("Ningún jugador registró predicción para este partido")
    st.stop()

pred_df = pd.DataFrame(pred_resp.data)

# -------------------------
# RESOLVER USERNAMES
# -------------------------
user_ids = pred_df["usuario_id"].unique().tolist()

users_resp = (
    supabase
    .table("users")
    .select("id, username")
    .in_("id", user_ids)
    .execute()
)

user_map = {
    u["id"]: u["username"]
    for u in users_resp.data
}

pred_df["username"] = pred_df["usuario_id"].map(user_map)

df = pred_df.rename(columns={
    "home_score": "Local",
    "away_score": "Visitante",
    "winner": "Ganador"
})

# -------------------------
# FILTER JUGADORES
# -------------------------
jugadores_disponibles = df["username"].dropna().unique().tolist()

jugadores_seleccionados = st.multiselect(
    "Comparar con jugadores",
    options=jugadores_disponibles,
    default=jugadores_disponibles
)

df = df[df["username"].isin(jugadores_seleccionados)]

if df.empty:
    st.warning("No hay jugadores seleccionados para comparar")
    st.stop()

# -------------------------
# ORDENAR (yo primero)
# -------------------------
df["__orden"] = df["usuario_id"] != user_id
df = df.sort_values("__orden").drop(columns="__orden")

# -------------------------
# HIGHLIGHT MI PREDICCIÓN
# -------------------------
def highlight_user(row):
    if row["usuario_id"] == user_id:
        return ["background-color: #1f77b4; color: white"] * len(row)
    return [""] * len(row)

st.caption(f"Comparando {len(df)} predicciones")

st.dataframe(
    df[["username", "Local", "Visitante", "Ganador"]]
    .style
    .apply(highlight_user, axis=1),
    use_container_width=True
)
