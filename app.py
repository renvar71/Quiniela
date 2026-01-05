#app.py
import streamlit as st
import sqlite3
import os
import hashlib
from db import DB, create_database
from api import save_next_games, save_teams
from helpers_auth import save_login, load_login, logout

# siempre intenta cargar datos
create_database()
save_teams()
save_next_games()

st.set_page_config(initial_sidebar_state="collapsed")

# -------------------------
# SESSION INIT + COOKIES
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------
# AUTH HELPERS
# -------------------------
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(email, password_hash):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT password_hash FROM usuarios WHERE email = ?",
        (email,)
    )
    result = cur.fetchone()
    conn.close()
    return result and result[0] == password_hash

def add_user(nombre, email, password):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios (nombre, email, password_hash)
            VALUES (?, ?, ?)
        """, (nombre, email, hash_pw(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# -------------------------
# ACCESS (LOGIN / REGISTER)
# -------------------------
if not st.session_state.logged_in:

    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    st.title("🏈 Quiniela NFL")

    access = st.radio("Acceso", ["Iniciar sesión", "Crear usuario"])

    if access == "Iniciar sesión":
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")

        if st.button("Entrar"):
            if authenticate(email, hash_pw(password)):
                st.session_state.logged_in = True
                st.session_state.user = email
                save_login(email)        # 👈 guarda cookie
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

    else:
        nombre = st.text_input("Nombre")
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")

        if st.button("Crear cuenta"):
            if add_user(nombre, email, password):
                st.success("Usuario creado. Ya puedes iniciar sesión.")
            else:
                st.error("Ese email ya existe")

    st.stop()

# -------------------------
# NAVIGATION (POST LOGIN)
# -------------------------
st.sidebar.success(f"Bienvenid@ {st.session_state.user}")

if st.sidebar.button("Cerrar sesión"):
    logout()
    st.rerun()

pages = [
    st.Page("pages/main.py", title="Inicio"),
    st.Page("pages/tabla.py", title="Tabla"),
    st.Page("pages/menu_predicciones.py", title="Mis Predicciones"),
    st.Page("pages/prediccion_partido.py", title="Predicción")
]

pg = st.navigation(pages)

st.markdown("""
<style>
a[href*="prediccion_partido"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

pg.run()
