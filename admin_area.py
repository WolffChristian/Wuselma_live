from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DB_FILE = "wuselmap.db"

# Hilfsfunktion für SQLite-Verbindung
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Hilfsfunktion: Prüfen ob Nutzer Admin ist
def is_admin(request: Request):
    user = request.session.get("user")
    if not user:
        return False
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT rolle FROM nutzer WHERE benutzername = ?", (user,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row['rolle'] == 'admin':
        return True
    return False

@router.get("/admin", response_class=HTMLResponse)
async def show_admin(request: Request):
    if not is_admin(request):
        return RedirectResponse(url="/map?error=no_admin")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Daten für die Tabs direkt aus SQLite als Dictionaries laden
    cursor.execute("SELECT * FROM vorschlaege")
    vorschlaege = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT nutzer_id, benutzername, vorname, nachname, email, alter_wert, rolle FROM nutzer")
    nutzer = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM spielplaetze")
    plaetze = [dict(row) for row in cursor.fetchall()]
    
    conn.close()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "vorschlaege": vorschlaege,
        "nutzer": nutzer,
        "plaetze": plaetze
    })

# Route zum Freischalten eines Vorschlags
@router.post("/admin/approve/{v_id}")
async def approve_spot(v_id: int, request: Request):
    if not is_admin(request): 
        raise HTTPException(status_code=403, detail="Zutritt verweigert")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Vorschlag laden
    cursor.execute("SELECT * FROM vorschlaege WHERE id = ?", (v_id,))
    v = cursor.fetchone()
    
    if not v:
        conn.close()
        raise HTTPException(status_code=404, detail="Vorschlag nicht gefunden")
    
    # 2. In Haupttabelle 'spielplaetze' schieben
    cursor.execute("""
        INSERT INTO spielplaetze (
            standort, lat, lon, altersfreigabe, bundesland, plz, stadt, 
            bild_data, status, ausstattung, hat_schatten, hat_sitze, 
            hat_wc, adresse, hat_parkplatz
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'aktiv', ?, ?, ?, ?, ?, ?)
    """, (
        v['standort'], v['lat'], v['lon'], v['altersfreigabe'], 
        v['bundesland'], v['plz'], v['stadt'], v['bild_data'], 
        v['ausstattung'], v['hat_schatten'], v['hat_sitze'], 
        v['hat_wc'], v['adresse'], v['hat_parkplatz']
    ))
    
    # 3. Vorschlag löschen
    cursor.execute("DELETE FROM vorschlaege WHERE id = ?", (v_id,))
    
    conn.commit()
    conn.close()
    
    return RedirectResponse(url="/admin", status_code=303)