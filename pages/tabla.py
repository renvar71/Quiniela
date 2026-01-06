import streamlit as st
import pandas as pd
from supabase_config import supabase

# -------------------------
# SESSION CHECK
# -------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

st.title("📊 Tabla General")

# -------------------------
# OBTENER USUARIOS
# -------------------------
users_res = supabase.table("usuarios") \
    .select("id, nombre") \
    .execute()

users = users_res.data or []

# -------------------------
# OBTENER PUNTAJES
# -------------------------
scores_res = supabase.table("puntajes") \
    .select("usuario_id, puntos") \
    .execute()

scores = scores_res.data or []

# -------------------------
# CALCULAR RANKING
# -------------------------
data = []

for u in users:
    total_puntos = sum(
        s["puntos"] for s in scores
        if s["usuario_id"] == u["id"] and s["puntos"] is not None
    )

    data.append({
        "Usuario": u["nombre"],
        "Puntos": total_puntos
    })

df = pd.DataFrame(data)

# Ordenar por puntos
df = df.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

# -------------------------
# POSICIONES CON EMOJIS
# -------------------------
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

# -------------------------
# MOSTRAR TABLA
# -------------------------
st.table(df.style.hide(axis="index"))
