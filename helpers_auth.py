#helpers_auth.py
from streamlit_cookies_manager import EncryptedCookieManager
import streamlit as st

cookies = EncryptedCookieManager(
    prefix="quiniela_",
    password="cambia_esto_por_algo_seguro"
)

if not cookies.ready():
    st.stop()

def save_login(user):
    cookies["logged_in"] = "1"
    cookies["user"] = user
    cookies.save()

def load_login():
    if cookies.get("logged_in") == "1":
        st.session_state.logged_in = True
        st.session_state.user = cookies.get("user")

def logout():
    cookies.clear()
    st.session_state.clear()
