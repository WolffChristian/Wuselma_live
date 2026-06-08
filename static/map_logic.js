// 1. Initialisierung: Deutschlandweite Ansicht
const map = L.map('map', { zoomControl: false }).setView([51.1657, 10.4515], 6); 
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
let markerLayer = L.layerGroup().addTo(map);

// GLOBALER SPEICHER
window.currentSelectedId = null;

// Hilfsfunktion Distanz
function berechneDistanz(lat1, lon1, lat2, lon2) {
    const R = 6371; 
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

// Hauptfunktion zum Laden und Filtern
async function ladeMarker() {
    const eingabe = document.getElementById('suche').value.trim().toLowerCase();
    const maxDist = parseFloat(document.getElementById('filter-dist').value);
    const gewaehltesAlter = document.getElementById('filter-alter').value;
    
    markerLayer.clearLayers();
    if (typeof allePlaetze === 'undefined' || !allePlaetze) return;

    let gefundenesZentrum = null;

    if (eingabe.length >= 3) {
        // ZUERST: Prüfen, ob die Eingabe eine Postleitzahl ist oder einer Stadt entspricht
        const ortMatch = allePlaetze.find(p => 
            (p.plz && String(p.plz).trim() === eingabe) || 
            (p.stadt && p.stadt.toLowerCase().trim() === eingabe)
        );

        if (ortMatch) {
            // Direkt die exakten Koordinaten aus deiner Datenbank nutzen!
            gefundenesZentrum = {
                lat: parseFloat(String(ortMatch.lat).replace(',', '.')),
                lon: parseFloat(String(ortMatch.lon).replace(',', '.'))
            };
        } else {
            // Nur wenn es KEIN Match in deinen Daten ist, fragen wir die API als Backup
            try {
                const apiQuery = !isNaN(eingabe) ? eingabe + ", Deutschland" : eingabe;
                const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(apiQuery)}&countrycodes=de&limit=1`);
                const data = await res.json();
                if (data.length > 0) gefundenesZentrum = { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon) };
            } catch (e) { console.error("Geocoding Fehler:", e); }
        }
    }

    const bLat = gefundenesZentrum ? gefundenesZentrum.lat : 51.1657;
    const bLon = gefundenesZentrum ? gefundenesZentrum.lon : 10.4515;

    allePlaetze.forEach(p => {
        const lat = parseFloat(String(p.lat).replace(',', '.'));
        const lon = parseFloat(String(p.lon).replace(',', '.'));
        if (isNaN(lat) || isNaN(lon)) return;

        const d = berechneDistanz(bLat, bLon, lat, lon);
        const name = (p.standort || p.Standort || "").toLowerCase();
        const distPasst = (eingabe === "" && maxDist >= 50) ? true : d <= maxDist;
        const alterPasst = (gewaehltesAlter === "alle") || (p.altersfreigabe === gewaehltesAlter);

        if (distPasst && alterPasst) {
            // Erweiterter Abgleich: Zeige Marker, wenn Name, Stadt oder PLZ übereinstimmen, oder ein Zentrum gefunden wurde
            const plzString = p.plz ? String(p.plz) : "";
            const stadtString = p.stadt ? p.stadt.toLowerCase() : "";
            
            if (eingabe === "" || name.includes(eingabe) || plzString === eingabe || stadtString === eingabe || gefundenesZentrum) {
                L.marker([lat, lon]).addTo(markerLayer).on('click', () => zeigeDetails(p, lat, lon));
            }
        }
    });

    if (eingabe.length === 0) {
        map.flyTo([51.1657, 10.4515], 6);
    } else if (gefundenesZentrum && eingabe.length >= 3) {
        map.flyTo([gefundenesZentrum.lat, gefundenesZentrum.lon], 12);
    }
}

// Detail-Ansicht (Die Schaltzentrale)
async function zeigeDetails(p, lat, lon) {
    const s_id = p.id || p.ID;
    window.currentSelectedId = s_id; 

    // Elemente holen
    const detailsDiv = document.getElementById('details');
    const placeholder = document.getElementById('placeholder');
    const imgEl = document.getElementById('det-bild');
    const photoNote = document.getElementById('foto-hinweis');
    const favBtn = document.getElementById('fav-btn');

    // Sidebar umschalten
    if (placeholder) placeholder.style.display = 'none';
    if (detailsDiv) detailsDiv.style.display = 'block';

    // ID im Button verankern (Wie beim Upload!)
    if (favBtn) {
        favBtn.setAttribute('data-id', s_id);
        favBtn.innerHTML = "⭐ Favorit speichern";
        favBtn.disabled = false;
        favBtn.style.background = "";
    }

    // Bild-Logik
    if (imgEl) {
        if (p.bild_data && p.bild_data.length > 100) {
            imgEl.src = "data:image/jpeg;base64," + p.bild_data;
            if (photoNote) photoNote.style.display = 'none';
        } else {
            imgEl.src = '/static/Logo_Wuselmap.png';
            if (photoNote) photoNote.style.display = 'block';
        }
    }

    // Texte setzen
    document.getElementById('det-name').innerText = p.standort || p.Standort || "Spielplatz";
    document.getElementById('det-stadt').innerText = "📍 " + (p.adresse || "") + " " + (p.stadt || "");
    document.getElementById('det-alter').innerText = "👶 Alter: " + (p.altersfreigabe || "Alle");
    document.getElementById('det-navi').href = `https://www.google.com/maps?q=${lat},${lon}`;

    // Ausstattung
    const ausst = document.getElementById('det-ausstattung');
    if (ausst) {
        ausst.innerHTML = "";
        const tags = { hat_schatten: '⛱️ Schatten', hat_wc: '🚽 WC', hat_sitze: '🪑 Bänke', hat_parkplatz: '🚗 Parkplatz' };
        for (let k in tags) {
            if (p[k] == 1 || p[k] == "1") {
                ausst.innerHTML += `<span class="feature-tag" style="background:var(--main-turquois); border:1px solid var(--accent-gold); padding:5px 12px; border-radius:20px; margin-right:8px; display:inline-block; font-size:0.9rem; margin-bottom:5px;">${tags[k]}</span>`;
            }
        }
    }

    map.panTo([lat, lon]);

    // Wetter
    try {
        const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`);
        const data = await res.json();
        const temp = document.getElementById('wetter-temp');
        if (temp) temp.innerText = data.current_weather.temperature + "°C";
    } catch (e) { console.log("Wetter-Fehler"); }
}

// Event Listener
document.getElementById('suche').addEventListener('input', ladeMarker);
document.getElementById('filter-dist').addEventListener('input', (e) => {
    document.getElementById('dist-val').innerText = e.target.value;
    ladeMarker();
});
document.getElementById('filter-alter').addEventListener('change', ladeMarker);
document.getElementById('btn-suche-start').addEventListener('click', ladeMarker);

ladeMarker();