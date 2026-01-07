# tabla.py
import streamlit as st
import pandas as pd
from db import get_usuarios, get_puntajes

# -------------------------
# SESSION CHECK
# -------------------------
if not st.session_state.get("logged_in"):
    st.warning("Debes iniciar sesión")
    st.stop()

st.title("📊 Tabla General")

# -------------------------
# CACHE DE LECTURA
# -------------------------
@st.cache_data(ttl=30)
def load_tabla():
    usuarios = get_usuarios()
    puntajes = get_puntajes()

    data = []

    for u in usuarios:
        total_puntos = sum(
            p["puntos"]
            for p in puntajes
            if p["usuario_id"] == u["id"] and p["puntos"] is not None
        )

        data.append({
            "Usuario": u["nombre"],
            "Puntos": total_puntos
        })

    df = pd.DataFrame(data)

    if not df.empty:
        df = df.sort_values("Puntos", ascending=False).reset_index(drop=True)

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
# MOSTRAR TABLA
# -------------------------
df = load_tabla()

if df.empty:
    st.info("Aún no hay puntajes registrados")
else:
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True
    )
