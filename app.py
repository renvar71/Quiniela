# app.py
import streamlit as st
import hashlib
from db import get_user_id, hash_password, save_prediccion, get_prediccion_status
from api import save_next_games, save_teams
from supabase_config import supabase

# -------------------------
# INICIALIZACIÓN DE DATOS
# -------------------------
# Poblar equipos y próximos partidos desde API
save_teams()
save_next_games()

st.set_page_config(initial_sidebar_state="collapsed")

# -------------------------
# SESSION INIT
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------
# FUNCIONES DE LOGIN/REGISTRO
# -------------------------
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(email, password):
    pw_hash = hash_pw(password)
    res = supabase.table("usuarios").select("id")\
        .eq("email", email).eq("password_hash", pw_hash).single().execute()
    return res.data is not None

def add_user(nombre, email, password):
    pw_hash = hash_pw(password)
    try:
        supabase.table("usuarios").insert({
            "nombre": nombre,
            "email": email,
            "password_hash": pw_hash
        }).execute()
        return True
    except:
        return False

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None

# -------------------------
# LOGIN / REGISTRO
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

    else:  # Crear usuario
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
# POST LOGIN: SIDEBAR Y NAV
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
