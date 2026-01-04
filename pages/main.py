# ======================================================
# VERIFICAR TABLA predicciones
# ======================================================
import sqlite3
import streamlit as st

DB = "quiniela.db"  # misma ruta que usas en tu proyecto

def check_and_fix_predicciones():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Obtener columnas actuales
    cur.execute("PRAGMA table_info(predicciones)")
    columnas = [c[1] for c in cur.fetchall()]

    if "fecha_partido" not in columnas:
        cur.execute("ALTER TABLE predicciones ADD COLUMN fecha_partido TEXT")
        st.info("Columna 'fecha_partido' agregada automáticamente.")
    else:
        st.debug("Columna 'fecha_partido' ya existe.")

    conn.commit()
    conn.close()

# Ejecutar al inicio de la app
check_and_fix_predicciones()
