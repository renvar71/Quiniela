# app.py
import streamlit as st
import hashlib
from db import (
    supabase,
    get_user_id,
    hash_password,
)
from api import save_teams, save_next_games

# -------------------------
# Cargar datos iniciales solo una vez
# -------------------------
if "data_loaded" not in st.session_state:
    try:
        save_teams()
        save_next_games()
        st.session_state.data_loaded = True
    except Exception as e:
        st.error(f"Error cargando datos iniciales: {e}")

st.set_page_config(initial_sidebar_state="collapsed")

# -------------------------
# SESSION INIT
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------
# AUTH HELPERS
# -------------------------
def authenticate_user(email, password):
    user_id = get_user_id(email)
    if not user_id:
        return False
    # Recuperar password hash desde Supabase
    res = supabase.table("usuarios").select("password_hash").eq("id", user_id).single().execute()
    if not res.data:
        return False
    return res.data["password_hash"] == hash_password(password)

def add_user(nombre, email, password):
    try:
        supabase.table("usuarios").insert([{
            "nombre": nombre,
            "email": email,
            "password_hash": hash_password(password)
        }]).execute()
        return True
    except Exception:
        return False

# -------------------------
# LOGIN / REGISTER
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
            if authenticate_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user = email
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
                st.error("Ese email ya existe o hubo un error")

    st.stop()

# -------------------------
# NAVIGATION (POST LOGIN)
# -------------------------
st.sidebar.success(f"Bienvenid@ {st.session_state.user}")

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None

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
st.markdown("""
<style>
a[href*="prediccion_partido"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

pg.run()
