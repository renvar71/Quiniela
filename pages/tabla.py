# tabla.py
import streamlit as st
import pandas as pd
# Quitamos cliente global
# from supabase_config import supabase
# Importamos funciones nuevas
from db import WEEK_TITLES, get_usuarios, get_puntajes

# -------------------------
# SESSION CHECK
# -------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

st.title("📊 Tabla General")

# QUITAMOS QUERIES Y REVISAMOS SESSIONSTATE PARA CREAR CACHE
# # -------------------------
# # OBTENER USUARIOS
# # -------------------------
# users_res = supabase.table("usuarios") \
#     .select("id, nombre") \
#     .execute()

# users = users_res.data or []
# -------------------------
# CACHE DE USUARIOS
# -------------------------
if "usuarios_cache" not in st.session_state:
    st.session_state.usuarios_cache = get_usuarios()

users = st.session_state.usuarios_cache
# # -------------------------
# # OBTENER PUNTAJES
# # -------------------------
# scores_res = supabase.table("puntajes") \
#     .select("usuario_id, puntos, semana") \
#     .execute()

# scores = scores_res.data or []
# -------------------------
# CACHE DE PUNTAJES
# -------------------------
if "puntajes_cache" not in st.session_state:
    st.session_state.puntajes_cache = get_puntajes()

scores = st.session_state.puntajes_cache

# -------------------------
# SEMANAS DISPONIBLES
# -------------------------
semanas_disponibles = sorted({s["semana"] for s in scores if s["puntos"] is not None})

# Orden manual de las columnas para la vista general
orden_columnas = [160, 125, 150, 200]  # Ronda Comodines, Ronda Divisional, Campeón de Conferencia, Super Bowl

# -------------------------
# SELECTBOX VISTA
# -------------------------
# Crear dos columnas: la primera vacía, la segunda para el selectbox
col1, col2 = st.columns([3, 1]) 
with col2:
    vista = st.selectbox("", ["General"] + [str(w) for w in semanas_disponibles])


# -------------------------
# FUNCIÓN PARA CALCULAR POSICIONES CON EMOJIS
# -------------------------
def calcular_posiciones(df):
    posiciones = []
    for i in range(len(df)):
        if i == 0:
            posiciones.append("🥇 1")
        elif i == 1:
            posiciones.append("🥈 2")
        elif i == 2:
            posiciones.append("🥉 3")
        else:
            posiciones.append(str(i + 1))
    df.insert(0, "Posición", posiciones)
    return df

# -------------------------
# VISTA GENERAL O POR SEMANA
# -------------------------
if vista == "General":
    # Usar orden manual
    todas_semanas = orden_columnas

    data = []
    for u in users:
        row = {"Usuario": u["nombre"]}
        total = 0
        for semana in todas_semanas:
            puntos_semana = sum(
                s["puntos"] for s in scores
                if s["usuario_id"] == u["id"] and s["semana"] == semana and s["puntos"] is not None
            )
            total += puntos_semana
            col_name = WEEK_TITLES.get(semana, f"Semana {semana}")
            row[col_name] = puntos_semana
        row["Total"] = total
        data.append(row)

    df = pd.DataFrame(data)
    df = df.sort_values(by="Total", ascending=False).reset_index(drop=True)
    df = calcular_posiciones(df)

else:
    # Vista de semana específica
    semana_sel = int(vista)
    data = []
    for u in users:
        puntos_semana = sum(
            s["puntos"] for s in scores
            if s["usuario_id"] == u["id"] and s["semana"] == semana_sel and s["puntos"] is not None
        )
        data.append({
            "Usuario": u["nombre"],
            "Puntos": puntos_semana
        })

    if not any(d["Puntos"] > 0 for d in data):
        st.info(f"No hay puntaje de la semana {semana_sel} todavía.")
        st.stop()

    df = pd.DataFrame(data)
    # Ordenar por puntos
    df = df.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    df = calcular_posiciones(df)

# -------------------------
# MOSTRAR TABLA
# -------------------------
st.dataframe(
    df,
    hide_index=True,
    use_container_width=True
)
