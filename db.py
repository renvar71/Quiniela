import sqlite3
import hashlib
from datetime import datetime, timedelta
from config import TEST_MODE

DB = "quiniela.db"  # base de datos local en el proyecto

def create_database():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS equipos (
        team_id TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        badge_url TEXT,
        logo_url TEXT
    );

    CREATE TABLE IF NOT EXISTS partidos (
        partido_id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_id TEXT UNIQUE,
        semana INTEGER NOT NULL,
        fecha DATETIME,
        home_badge_url TEXT,
        away_badge_url TEXT,
        equipo_local_id TEXT NOT NULL,
        equipo_visitante_id TEXT NOT NULL,
        estadio TEXT,
        status TEXT DEFAULT 'scheduled',
        FOREIGN KEY(equipo_local_id) REFERENCES equipos(team_id),
        FOREIGN KEY(equipo_visitante_id) REFERENCES equipos(team_id)
    );

    CREATE TABLE IF NOT EXISTS predicciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        partido_id INTEGER NOT NULL,
        semana INTEGER NOT NULL,
        pick TEXT NOT NULL,
        score_local INTEGER,
        score_away INTEGER,
        line_over_under TEXT,
        extra_question TEXT,
        fecha_prediccion DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_partido TEXT NOT NULL,
        UNIQUE(usuario_id, partido_id)
    );

    CREATE TABLE IF NOT EXISTS puntajes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id TEXT NOT NULL,
        partido_id INTEGER NOT NULL,
        semana INTEGER NOT NULL,
        puntos INTEGER NOT NULL,
        fecha_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(usuario_id, partido_id)
    );
    """)

    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_partidos(semana=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if semana:
        cur.execute("SELECT * FROM partidos WHERE semana = ?", (semana,))
    else:
        cur.execute("SELECT * FROM partidos")
    rows = cur.fetchall()
    conn.close()
    return rows

def save_prediccion(user_id, partido_id, semana, fecha_del_partido,
                    pick, score_local=None, score_away=None,
                    line_over_under=None, extra_question=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predicciones (
            usuario_id, partido_id, semana, pick, score_local, score_away,
            line_over_under, extra_question, fecha_partido
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, partido_id, semana, pick, score_local, score_away,
          line_over_under, extra_question, fecha_del_partido))
    conn.commit()
    conn.close()

def save_puntaje(usuario_id, partido_id, semana, puntos):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO puntajes (
            usuario_id, partido_id, semana, puntos
        ) VALUES (?, ?, ?, ?)
    """, (usuario_id, partido_id, semana, puntos))
    conn.commit()
    conn.close()

def has_prediccion(usuario_id, partido_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM predicciones
        WHERE usuario_id = ? AND partido_id = ?
    """, (usuario_id, partido_id))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def get_prediccion_status(user_id, partido_id, fecha_partido):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    SELECT p.fecha
    FROM predicciones pr
    JOIN partidos p ON p.partido_id = pr.partido_id
    WHERE pr.usuario_id = ? AND pr.partido_id = ?
""", (user_id, partido_id))
    row = cur.fetchone()
    conn.close()
    
    if TEST_MODE:
        return "🟢 Registrada" if exists else "🟡 Pendiente"
        
    if row:
        db_fecha = row[0]
        if db_fecha:
            try:
                partido_dt = datetime.fromisoformat(db_fecha)
                if datetime.now() >= partido_dt - timedelta(minutes=1):
                    return "🔴 Expirada"
                else:
                    return "🟢 Registrada"
            except ValueError:
                return "🟢 Registrada"
        return "🟢 Registrada"

    # si no hay registro
    if fecha_partido:
        try:
            partido_dt = datetime.fromisoformat(fecha_partido)
            if datetime.now() >= partido_dt - timedelta(minutes=1):
                return "🔴 Expirada"
        except ValueError:
            pass

    return "🟡 Pendiente"


def get_user_id(email):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
