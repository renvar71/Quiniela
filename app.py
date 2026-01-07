# app.py
import streamlit as st

from api import save_teams, save_next_games
from db import (
    authenticate_user,
    create_user
)

st.set_page_config(initial_sidebar_state="collapsed")

# -------------------------
# SESSION INIT
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user" not in st.session_state:
    st.session_state.user = None

# -------------------------
# LOGIN / REGISTER
# -------------------------
if not st.session_state.logged_in:

    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🏈 Quiniela NFL")

    access = st.radio("Acceso", ["Iniciar sesión", "Crear usuario"])

    if access == "Iniciar sesión":
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")

        if st.button("Entrar"):
            user_id = authenticate_user(email, password)

            if user_id:
                st.session_state.logged_in = True
                st.session_state.user = email
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

    else:
        nombre = st.text_input("Nombre")
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")

        if st.button("Crear cuenta"):
            ok = create_user(nombre, email, password)

            if ok:
                st.success("Usuario creado. Ya puedes iniciar sesión.")
            else:
                st.error("Ese email ya existe o hubo un error")

    st.stop()

# -------------------------
# DATA LOAD (ONCE PER SESSION)
# -------------------------
if "data_loaded" not in st.session_state:

    save_teams()

    partidos = save_next_games()

    if not partidos:
        st.info("⏳ Esperando agenda de próximos partidos...")
    else:
        st.success(f"📅 {len(partidos)} partidos cargados")

    st.session_state.data_loaded = True

# -------------------------
# NAVIGATION (POST LOGIN)
# -------------------------
st.sidebar.success(f"Bienvenid@ {st.session_state.user}")

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.user_id = None

if st.sidebar.button("Cerrar sesión"):
    logout()
    st.rerun()

# -------------------------
# PAGES
# -------------------------
pages = [
    st.Page("pages/main.py", title="Inicio"),
    st.Page("pages/tabla.py", title="Tabla"),
    st.Page("pages/menu_predicciones.py", title="Mis Predicciones"),
    st.Page("pages/prediccion_partido.py", title="Predicción")
]

pg = st.navigation(pages)

# Ocultar link directo a predicción
st.markdown(
    """
    <style>
    a[href*="prediccion_partido"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

pg.run()
