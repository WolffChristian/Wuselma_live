from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import os
import shutil
import requests
import hashlib
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite Datenbank-Pfad (wird lokal im Projektverzeichnis erstellt)
DB_FILE = "wuselmap.db"

# Hilfsfunktion für die Verbindung zur lokalen SQLite-Datenbank
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    # Zeilen als Dictionary zurückgeben (wie cursor(dictionary=True) in MySQL)
    conn.row_factory = sqlite3.Row
    return conn

# Automatische Initialisierung der Tabellen beim ersten Start
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Nutzer-Tabelle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nutzer (
            nutzer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzername TEXT UNIQUE NOT NULL,
            vorname TEXT,
            nachname TEXT,
            email TEXT UNIQUE NOT NULL,
            passwort TEXT NOT NULL,
            alter_wert INTEGER,
            rolle TEXT DEFAULT 'user'
        )
    """)
    
    # Vorschläge-Tabelle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vorschlaege (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            standort TEXT NOT NULL,
            stadt TEXT NOT NULL,
            status TEXT DEFAULT 'Prüfen'
        )
    """)
    
    # Feedback-Tabelle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nutzer_id INTEGER,
            nachricht TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# Datenbank beim Serverstart initialisieren
init_db()

# Hilfsfunktion für Passwort-Hashing
def hash_pw(pw):
    return hashlib.sha256(str.encode(pw)).hexdigest()

# --- DATEN-MODELLE ---
class LoginData(BaseModel):
    username: str
    password: str

class FeedbackData(BaseModel):
    nutzer_id: int
    nachricht: str

# --- ROUTEN ---

@app.post("/login")
def login(data: LoginData):
    # Admin-Check über .env
    if data.username == os.getenv("ADMIN_USER") and data.password == os.getenv("ADMIN_PASSWORD"):
        return {"status": "success", "rolle": "admin", "nutzer_id": 0}
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        hashed = hash_pw(data.password)
        # SQLite nutzt '?' als Platzhalter anstelle von '%s'
        query = "SELECT * FROM nutzer WHERE benutzername = ? AND passwort = ?"
        cursor.execute(query, (data.username, hashed))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {"status": "success", "rolle": user['rolle'], "nutzer_id": user['nutzer_id']}
        return {"status": "error", "message": "Zugriff verweigert"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/wetter/{lat}/{lon}")
def get_weather(lat: float, lon: float):
    api_key = os.getenv("OPENWEATHER_KEY") 
    if not api_key:
        return {"error": "API Key fehlt im Backend"}
        
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=de"
    return requests.get(url).json()

# --- ADMIN-LÖSCHFUNKTIONEN ---
@app.delete("/admin/feedback/{f_id}")
def delete_feedback(f_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM feedback WHERE id = ?", (f_id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/vorschlag/{p_id}")
def delete_vorschlag(p_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vorschlaege WHERE id = ?", (p_id,))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))