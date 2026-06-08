import os
import io
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from admin_area import router as admin_router
import database_manager as db

# 1. Router importieren
try:
    from routes_community import router as community_router
except ImportError:
    print("Fehler: Die Datei routes_community.py wurde nicht gefunden!")

# 2. FastAPI App definieren
app = FastAPI()

# 3. Sicherheits-Key für Sessions
app.add_middleware(SessionMiddleware, secret_key="dein_geheimnis_carlos_123")

# 4. Router einbinden
app.include_router(community_router)
app.include_router(admin_router)

# 5. Pfade und Verzeichnisse setzen
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --- HILFSFUNKTION FÜR NAVIGATION (ROTER PUNKT) ---
def get_nav_context(request: Request, user: str):
    anzahl = db.zaehle_ungelesene(user) if user else 0
    return {"request": request, "anzahl_neu": anzahl, "user": user}

# --- LOGIN & AUTH ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("logged_in"): 
        return RedirectResponse(url="/map")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    u = username.lower().strip()
    nutzer_liste = db.hole_df("nutzer")
    
    # Nutzer in der Liste via reinem Python suchen
    user_row = next((n for n in nutzer_liste if n['benutzername'] == u), None)
    
    if user_row:
        # Passwort checken (nutzt jetzt die Hashing-Funktion aus db_users via app.py Logik)
        from db_users import hash_passwort
        if user_row['passwort'] == hash_passwort(password):
            request.session["logged_in"] = True
            request.session["user"] = u
            request.session["role"] = str(user_row.get('rolle', 'user')).lower().strip()
            
            print(f"Login erfolgreich: {u} mit Rolle: {request.session['role']}")
            return RedirectResponse(url="/map", status_code=303)
            
    return templates.TemplateResponse("login.html", {"request": request, "error": "Fehler beim Login"})

# --- REGISTRIERUNG ---
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(request: Request, username: str=Form(...), password: str=Form(...), email: str=Form(...), vorname: str=Form(...), nachname: str=Form(...), alter: int=Form(...)):
    nutzer_liste = db.hole_df("nutzer")
    
    # Prüfen ob Name vergeben ist
    if any(n['benutzername'].lower() == username.lower() for n in nutzer_liste):
        return templates.TemplateResponse("register.html", {"request": request, "error": "Name vergeben!"})
    
    from db_users import registriere_nutzer
    if registriere_nutzer(username, password, email, vorname, nachname, alter, agb=1):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "error": "Fehler"})

# --- KARTE ---
@app.get("/map", response_class=HTMLResponse)
async def show_map(request: Request):
    user = request.session.get("user")
    if not request.session.get("logged_in"): 
        return RedirectResponse(url="/")
    
    plaetze = db.hole_df("spielplaetze")
    ctx = get_nav_context(request, user)
    ctx.update({"plaetze": plaetze})
    return templates.TemplateResponse("karte.html", ctx)

# --- FUNK (ÖFFENTLICH) ---
@app.get("/funk", response_class=HTMLResponse)
async def show_funk(request: Request):
    user = request.session.get("user")
    if not request.session.get("logged_in"): 
        return RedirectResponse(url="/")
    
    nutzer_liste = db.hole_df("nutzer")
    user_data = next((n for n in nutzer_liste if n['benutzername'] == user), {})
    
    public_msg = db.hole_nachrichten(user, nur_privat=False)
    plaetze = db.hole_df("spielplaetze")
    spot_namen = [p['Standort'] for p in plaetze]

    ctx = get_nav_context(request, user)
    ctx.update({
        "user_data": user_data,
        "public_msg": public_msg,
        "spot_namen": spot_namen
    })
    return templates.TemplateResponse("funk.html", ctx)

@app.post("/sende_funk")
async def sende_funk(request: Request, nachricht: str=Form(...), spot: str=Form("Allgemein"), is_private: bool=Form(False), ziel: str=Form("GLOBAL")):
    user = request.session.get("user")
    if not user: 
        return RedirectResponse(url="/", status_code=303)
    
    db.sende_nachricht(von=user, ziel=ziel, nachricht=nachricht, is_private=is_private, spot_name=spot)
    return RedirectResponse(url="/crew" if is_private else "/funk", status_code=303)

# --- CREW & WUSELFUNK ---
@app.get("/crew", response_class=HTMLResponse)
async def show_crew(request: Request):
    user = request.session.get("user")
    if not request.session.get("logged_in"): 
        return RedirectResponse(url="/")
    
    db.markiere_als_gelesen(user)
    freunde = db.hole_freundesliste(user)
    privat_msg = db.hole_nachrichten(user, nur_privat=True)
    
    ctx = get_nav_context(request, user)
    ctx.update({
        "freunde": freunde,
        "privat_msg": privat_msg,
        "anfragen": [] 
    })
    return templates.TemplateResponse("crew.html", ctx)

@app.post("/suche_crew")
async def suche_crew(request: Request, suche: str=Form(...)):
    user = request.session.get("user")
    if not user: 
        return RedirectResponse(url="/", status_code=303)
    
    nutzer_liste = db.hole_df("nutzer")
    s = suche.lower()
    treffer = [
        n for n in nutzer_liste 
        if s in n['benutzername'].lower() or (n['vorname'] and s in n['vorname'].lower())
    ]
    
    ctx = get_nav_context(request, user)
    ctx.update({
        "treffer": treffer, 
        "freunde": db.hole_freundesliste(user),
        "privat_msg": [],
        "anfragen": []
    })
    return templates.TemplateResponse("crew.html", ctx)

@app.post("/einladen/{freund_name}")
async def einladen(request: Request, freund_name: str):
    user = request.session.get("user")
    if user:
        db.fuege_freund_hinzu(user, freund_name)
    return RedirectResponse(url="/crew", status_code=303)

# --- PROFIL ---
@app.get("/profil", response_class=HTMLResponse)
async def show_profile(request: Request):
    user = request.session.get("user")
    if not user: 
        return RedirectResponse(url="/", status_code=303)
    
    nutzer_liste = db.hole_df("nutzer")
    user_data = next((n for n in nutzer_liste if n['benutzername'] == user), {})
    favoriten = db.hole_favoriten_details(user)

    ctx = get_nav_context(request, user)
    ctx.update({"user_data": user_data, "favoriten": favoriten})
    return templates.TemplateResponse("profil.html", ctx)

@app.post("/update_profil")
async def update_profil(request: Request, email: str=Form(...), vorname: str=Form(...), nachname: str=Form(...), alter: int=Form(...), emoji: str=Form(...)):
    user = request.session.get("user")
    if user: 
        db.aktualisiere_profil(user, email, vorname, nachname, alter, emoji)
    return RedirectResponse(url="/profil", status_code=303)

# --- AVATAR-UPLOAD ---
@app.post("/update_avatar")
async def update_avatar(request: Request, avatar_file: UploadFile = File(...)):
    user = request.session.get("user")
    if not user: 
        return RedirectResponse(url="/", status_code=303)
    
    contents = await avatar_file.read()
    if contents:
        print(f"Datei erhalten: {avatar_file.filename} für User {user}")
        
    return RedirectResponse(url="/profil", status_code=303)

# --- FEEDBACK ---
@app.post("/send_feedback")
async def send_feedback(request: Request, feedback_text: str = Form(...)):
    user = request.session.get("user") or "Anonym"
    # Parameter an deine SQLite-Struktur angepasst (von, ziel, nachricht)
    db.sende_nachricht(von=user, ziel="ADMIN", nachricht=f"[FEEDBACK] {feedback_text}", is_private=True, spot_name="System")
    return RedirectResponse(url="/profil", status_code=303)

# --- FAVORITEN ---
@app.post("/add_favorit")
async def add_favorit(request: Request, spielplatz_id: str = Form(...)):
    user = request.session.get("user")
    if not user: 
        return {"status": "error", "message": "Nicht eingeloggt"}
    
    try:
        s_id = int(spielplatz_id)
        erfolg = db.speichere_favorit(user, s_id)
        return {"status": "success" if erfolg else "error"}
    except Exception as e:
        print(f"Fehler beim Favorit-Zuweisen: {e}")
        return {"status": "error", "message": str(e)}

# --- BEWERTUNGEN ---
@app.post("/bewerten")
async def bewerten(request: Request, spielplatz_id: str = Form(...), sterne: str = Form(...), kommentar: str = Form("")):
    user = request.session.get("user")
    if not user: 
        return {"status": "error", "message": "Nicht eingeloggt"}
    
    try:
        s_id = int(spielplatz_id)
        sterne_int = int(sterne)
        erfolg = db.speichere_bewertung(s_id, user, sterne_int, kommentar)
        return {"status": "success" if erfolg else "error"}
    except Exception as e:
        print(f"Fehler beim Bewerten: {e}")
        return {"status": "error", "message": str(e)}

# --- RECHTLICHES, IMPRESSUM & DATENSCHUTZ ---
@app.get("/rechtliches", response_class=HTMLResponse)
async def show_legal(request: Request):
    user = request.session.get("user")
    ctx = get_nav_context(request, user)
    return templates.TemplateResponse("rechtliches.html", ctx)

# --- SONSTIGES ---
@app.post("/accept_agb")
async def accept_agb(request: Request):
    user = request.session.get("user")
    if not user: 
        return RedirectResponse(url="/", status_code=303)
    db.aktualisiere_eintrag("nutzer", user, {"agb_version": 2}) 
    return RedirectResponse(url="/map", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

# --- SERVER START ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)