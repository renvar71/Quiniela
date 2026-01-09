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

st.title("👥 Comparación de Picks")

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

# recuperar el número de semana seleccionado
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
    .select(
        "id, home_team, away_team, status"
    )
    .eq("semana", semana)
    .eq("status", "finished")
    .execute()
)

partidos_df = pd.DataFrame(partidos_resp.data)

if partidos_df.empty:
    st.warning("No hay partidos finalizados para esta semana")
    st.stop()

partidos_df["label"] = (
    partidos_df["home_team"] + " vs " + partidos_df["away_team"]
)

partido_label = st.selectbox(
    "Partido",
    options=[None] + partidos_df["label"].tolist()
)

if not partido_label:
    st.info("Selecciona un partido finalizado")
    st.stop()

partido_id = partidos_df.loc[
    partidos_df["label"] == partido_label, "id"
].iloc[0]

# -------------------------
# FETCH PREDICCIONES
# -------------------------
pred_resp = (
    supabase
    .table("predicciones")
    .select(
        "user_id, home_score, away_score, winner, users(username)"
    )
    .eq("match_id", partido_id)
    .execute()
)

if not pred_resp.data:
    st.warning("Ningún jugador registró predicción para este partido")
    st.stop()

# Normalizar data
rows = []
for r in pred_resp.data:
    rows.append({
        "user_id": r["user_id"],
        "username": r["users"]["username"],
        "Local": r["home_score"],
        "Visitante": r["away_score"],
        "Ganador": r["winner"]
    })

df = pd.DataFrame(rows)

# -------------------------
# FILTER JUGADORES
# -------------------------
jugadores_disponibles = df["username"].unique().tolist()

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
# HIGHLIGHT MI PREDICCIÓN
# -------------------------
def highlight_user(row):
    if row["user_id"] == user_id:
        return ["background-color: #1f77b4; color: white"] * len(row)
    return [""] * len(row)

df_display = df.copy()
df_display = df_display.sort_values(
    by=["user_id"],
    key=lambda x: x != user_id
)

st.caption(f"Comparando {len(df_display)} predicciones")

st.dataframe(
    df_display
    .style
    .apply(highlight_user, axis=1),
    use_container_width=True
)
