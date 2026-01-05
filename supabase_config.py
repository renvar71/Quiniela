# supabase_config.py
from supabase import create_client, Client
import os

SUPABASE_URL = "https://rkvmhnjelpboagqjvdgo.supabase.co"
SUPABASE_KEY = "sb_publishable_Xd5COGbn7rx7hz6eVdgwtw_uWlF48pr"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

