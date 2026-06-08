from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import database_manager as db
import io

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/einsenden", response_class=HTMLResponse)
async def show_einsenden(request: Request):
    if not request.session.get("logged_in"): 
        return RedirectResponse(url="/")
        
    user = request.session.get("user")
    return templates.TemplateResponse("einsenden.html", {"request": request, "user": user})

@router.post("/neuer_spot")
async def neuer_spot(
    request: Request,
    name: str = Form(...),
    adresse: str = Form(...),
    stadt: str = Form(...),
    plz: str = Form(...),
    alter: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...),
    schatten: int = Form(0),
    sitze: int = Form(0),
    wc: int = Form(0),
    parken: int = Form(0),
    check_personen: str = Form(None), 
    check_rechte: str = Form(None),
    bild: UploadFile = File(None)
):
    # Sicherheits-Check für die rechtlichen Haken
    if not check_personen or not check_rechte:
        return RedirectResponse(url="/einsenden?error=rechtliches", status_code=303)

    bild_data = None
    if bild and bild.filename:
        content = await bild.read()
        bild_data = db.optimiere_bild(io.BytesIO(content))

    # Speichern in der lokalen SQLite vorschlaege-Tabelle über den database_manager
    erfolg = db.sende_vorschlag(
        name, adresse, alter, "Niedersachsen", plz, stadt, 
        bild_data, 1, "offen", schatten, sitze, wc, lat, lon, parken
    )
    
    # Nach Erfolg zurück zur Karte
    return RedirectResponse(url="/map?status=gesendet", status_code=303)