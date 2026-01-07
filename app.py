# app.py
import streamlit as st
from db import hash_password
# from db import supabase
# Importamos solamente la herramienta de creación del cliente para bajarlo a nivel de sesión en vez de global
from supabase_config import create_client
import os

st.set_page_config(initial_sidebar_state="collapsed")

from api import save_teams, save_next_games

# -------------------------
# SESSION INIT
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None
# -------------------------
# SUPABASE CLIENT (SESSION SCOPED)
# -------------------------
# Antes de autentificar se verifica si se encuentra a nivel sesión y se crea
if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"]
    )
# -------------------------
# AUTH HELPERS
# -------------------------
def authenticate_user(email, password):
    # res = supabase.table("usuarios") \
    #     .select("id, password_hash") \
    #     .eq("email", email) \
    #     .execute()
    # USAR EL CLIENTE DESDE SESIÓN EN AUTH
    res = st.session_state.supabase.table("usuarios") \
        .select("id, password_hash") \
        .eq("email", email) \
        .execute()


    if not res.data or len(res.data) == 0:
        return None

    user = res.data[0]

    if user["password_hash"] == hash_password(password):
        return user["id"]
    return None

def add_user(nombre, email, password):
    try:
        # MISMO CAMBIO AQUÍ
        st.session_state.supabase.table("usuarios").insert([{
            "nombre": nombre,
            "email": email,
            "password_hash": hash_password(password)
        }]).execute()
        return True
    except Exception:
        return False
    #     supabase.table("usuarios").insert([{
    #         "nombre": nombre,
    #         "email": email,
    #         "password_hash": hash_password(password)
    #     }]).execute()
    #     return True
    # except Exception:
    #     return False

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
            if add_user(nombre, email, password):
                st.success("Usuario creado. Ya puedes iniciar sesión.")
            else:
                st.error("Ese email ya existe o hubo un error")

    st.stop()

# -------------------------
# Cargar datos iniciales solo una vez
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
st.markdown("""
<style>
a[href*="prediccion_partido"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

pg.run()
