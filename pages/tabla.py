import streamlit as st
import sqlite3
from db import DB
import pandas as pd
from logic import calcular_puntajes_partido

# -------------------------
# SESSION CHECK
# -------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Debes iniciar sesión")
    st.stop()

st.title("📊 Tabla General")
# -------------------------
# TEST MODE – RECALCULAR PUNTAJES
# -------------------------
if st.session_state.get("test_mode", False):

    st.markdown("### 🧪 Modo de prueba")

    if st.button("🔄 Recalcular puntajes (TEST MODE)"):

        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        # obtener partidos con predicciones
        cur.execute("""
            SELECT DISTINCT partido_id
            FROM predicciones
        """)
        partidos = [p[0] for p in cur.fetchall()]

        for partido_id in partidos:
            resultados = calcular_puntajes_partido(partido_id)

            for r in resultados:
                cur.execute("""
                    INSERT OR REPLACE INTO puntajes
                    (usuario_id, partido_id, puntos)
                    VALUES (?, ?, ?)
                """, (r["user_id"], r["partido_id"], r["puntos"]))

        conn.commit()
        conn.close()

        st.success("✅ Puntajes recalculados usando partidos históricos")
        st.rerun()
# -------------------------
# OBTENER RANKING
# -------------------------
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
    SELECT 
        u.nombre AS Usuario,
        COALESCE(SUM(p.puntos), 0) AS Puntos
    FROM usuarios u
    LEFT JOIN puntajes p ON u.email = p.usuario_id
    GROUP BY u.nombre
    ORDER BY Puntos DESC
""")

ranking = cur.fetchall()
conn.close()

# -------------------------
# MOSTRAR TABLA
# -------------------------
df = pd.DataFrame(ranking, columns=["Usuario", "Puntos"])

# Agregar columna de posición con emojis
posiciones = []
for i, puntos in enumerate(df["Puntos"], start=1):
    if i == 1:
        posiciones.append(f"🥇 1")
    elif i == 2:
        posiciones.append(f"🥈 2")
    elif i == 3:
        posiciones.append(f"🥉 3")
    else:
        posiciones.append(str(i))
df.insert(0, "Posición", posiciones)

st.table(df)

