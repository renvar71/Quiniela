# supabase_config.py
from supabase import create_client, Client
import os

# Usa las variables de entorno en Streamlit Cloud
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
