# jugadores.py
import streamlit as st
import pandas as pd
from supabase_config import supabase
from db import WEEK_TITLES
from datetime import datetime, timezone
from logic import calcular_ganador_nombre

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
semana_labels = {s: WEEK_TITLES.get(s, f"Semana {s}") for s in semanas}

semana_label = st.selectbox("Semana", options=[None] + list(semana_labels.values()))
if not semana_label:
    st.stop()

semana = next(k for k, v in semana_labels.items() if v == semana_label)

# -------------------------
# SELECT PARTIDO (INICIADOS)
# -------------------------
partidos_resp = (
    supabase
    .table("partidos")
    .select(
        "id_partido, equipo_local_id, equipo_visitante_id, fecha, score_local, score_away"
    )
    .eq("semana", semana)
    .execute()
)

partidos_df = pd.DataFrame(partidos_resp.data)
partidos_df["fecha"] = pd.to_datetime(partidos_df["fecha"], utc=True)

now = datetime.now(timezone.utc)
partidos_df = partidos_df[partidos_df["fecha"] <= now]

if partidos_df.empty:
    st.warning("Aún no hay partidos iniciados para esta semana")
    st.stop()

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

partido_label = st.selectbox("Partido", options=[None] + partidos_df["label"].tolist())
if not partido_label:
    st.stop()

partido_row = partidos_df.loc[partidos_df["label"] == partido_label].iloc[0]
partido_id = partido_row["id_partido"]

# -------------------------
# GANADOR REAL (DESDE PARTIDOS)
# -------------------------
partido = {
    "score_local": partido_row["score_local"],
    "score_away": partido_row["score_away"],
    "equipo_local_id": partido_row["equipo_local_id"],
    "equipo_visitante_id": partido_row["equipo_visitante_id"],
}

ganador_real = calcular_ganador_nombre(partido)

# -------------------------
# FETCH RESULTADOS ADMIN
# -------------------------
res_admin = (
    supabase
    .table("resultados_admin")
    .select(
        "o_u_resultado, pregunta1_resultado, pregunta2_resultado"
    )
    .eq("id_partido", partido_id)
    .execute()
)

resultados = res_admin.data[0] if res_admin.data else {}

# -------------------------
# FETCH PUNTAJES
# -------------------------
puntajes_resp = (
    supabase
    .table("puntajes")
    .select("usuario_id, puntos")
    .eq("partido_id", partido_id)
    .execute()
)

puntajes_df = pd.DataFrame(puntajes_resp.data) if puntajes_resp.data else pd.DataFrame()

# -------------------------
# FETCH PREDICCIONES
# -------------------------
pred_resp = (
    supabase
    .table("predicciones")
    .select(
        "usuario_id, score_local, score_away, pick, line_over_under, extra_question_1, extra_question_2"
    )
    .eq("id_partido", partido_id)
    .execute()
)

pred_df = pd.DataFrame(pred_resp.data)

pred_df = pred_df.merge(
    puntajes_df,
    on="usuario_id",
    how="left"
)

pred_df["Puntos"] = pred_df["puntos"].apply(
    lambda x: "En juego" if pd.isna(x) else int(x)
)

# -------------------------
# RESOLVER USUARIOS
# -------------------------
users_resp = (
    supabase
    .table("usuarios")
    .select("id, nombre")
    .in_("id", pred_df["usuario_id"].tolist())
    .execute()
)

user_map = {u["id"]: u["nombre"] for u in users_resp.data}
pred_df["username"] = pred_df["usuario_id"].map(user_map)

# -------------------------
# FORMATEAR DF
# -------------------------
df = pred_df.rename(columns={
    "score_local": "Local",
    "score_away": "Visitante",
    "pick": "Ganador",
    "line_over_under": "Linea",
    "extra_question_1": "Pregunta Extra 1",
    "extra_question_2": "Pregunta Extra 2"
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
# ORDEN
# -------------------------
df["_orden"] = df["Puntos"].apply(lambda x: -1 if x == "En juego" else x)
df = df.sort_values("_orden", ascending=False).drop(columns="_orden")
df = df.rename(columns={
    "username": "Nombre"
})

# -------------------------
# STYLER
# -------------------------
def style_row(row):
    styles = [""] * len(row)

    # 🎯 Marcador exacto
    marcador_exacto = (
        partido["score_local"] is not None
        and partido["score_away"] is not None
        and row["Marcador Local"] == partido["score_local"]
        and row["Marcador Visitante"] == partido["score_away"]
    )

    for i, col in enumerate(row.index):
        # 🥇 Dorado para marcador exacto
        if marcador_exacto and col in ["Marcador Local", "Marcador Visitante"]:
            styles[i] = "background-color: #f1c40f; color: black"
            continue

        # ✅ Respuestas correctas (verde)
        col_map = {
            "Ganador": ganador_real,
            "Linea": resultados.get("o_u_resultado"),
            "Pregunta Extra 1": resultados.get("pregunta1_resultado"),
            "Pregunta Extra 2": resultados.get("pregunta2_resultado"),
        }

        if col in col_map and col_map[col] is not None:
            if row[col] == col_map[col]:
                styles[i] = "background-color: #2ecc71; color: black"

    # 👤 Usuario actual (azul si no tiene otro color)
    if df.loc[row.name, "usuario_id"] == user_id:
        styles = [
            s + "; background-color: #1f77b4; color: white"
            if s == ""
            else s
            for s in styles
        ]

    return styles


styled_df = (
    df[[
        "Nombre",
        "Local",
        "Visitante",
        "Ganador",
        "Linea",
        "Pregunta Extra 1",
        "Pregunta Extra 2",
        "Puntos"
    ]]
    .style
    .apply(style_row, axis=1)
)

st.caption(f"Comparando {len(df)} predicciones")
st.markdown(
    """
    <div style="display:flex; gap:20px; margin-bottom:10px;">
        <div>
            <span style="display:inline-block; width:16px; height:16px; background-color:#f1c40f; margin-right:6px;"></span>
            <strong>Marcador Exacto</strong>
        </div>
        <div>
            <span style="display:inline-block; width:16px; height:16px; background-color:#2ecc71; margin-right:6px;"></span>
            <strong>Pick correcto</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.dataframe(styled_df, use_container_width=True)
