import sqlite3
from PIL import Image
import io
import base64
import warnings
import mysql.connector
warnings.filterwarnings("ignore", category=UserWarning)



# Server-Konfiguration für die KletterDB
DB_CONFIG = {
    'host': '91.99.77.111',
    'port': 3306,
    'user': 'admin@wuselmap.de',
    'password': '%3Bd!Qj4!NMK6.%',
    'database': 'kletterdb'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Erfolgreich mit der KletterDB verbunden!")
        return conn
    except mysql.connector.Error as err:
        print(f"Fehler bei der Server-Verbindung: {err}")
        return None

# --- CORE CRUD ---
def hole_df(tabelle="spielplaetze"):
    """Gibt alle Einträge einer Tabelle als Liste von Dictionaries zurück (ersetzt Pandas)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {tabelle}")
        rows = cursor.fetchall()
        
        # Umwandlung in echte Dictionaries für dein Frontend
        ergebnis = []
        for row in rows:
            d = dict(row)
            # Groß-/Kleinschreibung-Fix aus deinem alten Skript für 'Standort'
            if 'standort' in d:
                d['Standort'] = d.pop('standort')
            ergebnis.append(d)
        return ergebnis
    except Exception as e:
        print(f"Fehler bei hole_df ({tabelle}): {e}")
        return []
    finally:
        conn.close()

def speichere_spielplatz(standort, lat, lon, altersfreigabe, bundesland, plz, stadt, bild_data, status, ausstattung, schatten, sitze, wc, adresse, parken):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """INSERT INTO spielplaetze (Standort, lat, lon, altersfreigabe, bundesland, plz, stadt, bild_data, status, ausstattung, hat_schatten, hat_sitze, hat_wc, adresse, hat_parkplatz) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    try:
        cursor.execute(sql, (standort, lat, lon, altersfreigabe, bundesland, plz, stadt, bild_data, status, ausstattung, schatten, sitze, wc, adresse, parken))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei speichere_spielplatz: {e}")
        return False
    finally:
        conn.close()

def loesche_eintrag(tabelle, e_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {tabelle} WHERE id = ?", (e_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei loesche_eintrag ({tabelle}): {e}")
        return False
    finally:
        conn.close()

def aktualisiere_eintrag(tabelle, e_id, daten):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # SQLite nutzt Backticks oder doppelte Anführungszeichen für Spaltennamen
        set_clause = ", ".join([f"`{k}`=?" for k in daten.keys()])
        values = list(daten.values())
        values.append(e_id)
        sql = f"UPDATE {tabelle} SET {set_clause} WHERE id = ?"
        cursor.execute(sql, tuple(values))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei aktualisiere_eintrag ({tabelle}): {e}")
        return False
    finally:
        conn.close()

# --- VORSCHLÄGE ---
def sende_vorschlag(n, ad, al, bund, plz, stadt, bild, ds, ausst="", sch=0, sitz=0, wc=0, lat=None, lon=None, parken=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """INSERT INTO vorschlaege (standort, adresse, altersfreigabe, bundesland, plz, stadt, bild_data, foto_datenschutz, ausstattung, hat_schatten, hat_sitze, hat_wc, status, lat, lon, hat_parkplatz) 
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'neu',?,?,?)"""
    try:
        cursor.execute(sql, (n, ad, al, bund, plz, stadt, bild, ds, ausst, sch, sitz, wc, lat, lon, parken))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei sende_vorschlag: {e}")
        return False
    finally:
        conn.close()

def optimiere_bild(bild_file):
    if bild_file is None: return None
    try:
        img = Image.open(bild_file)
        img.thumbnail((800, 800))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        return base64.b64encode(buffer.getvalue()).decode()
    except:
        return None

def loesche_spielplatz(s_id): 
    return loesche_eintrag("spielplaetze", s_id)

# --- FAVORITEN ---
def hole_favoriten_details(nutzername):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """
            SELECT s.* FROM spielplaetze s
            JOIN favoriten f ON s.id = f.spielplatz_id
            WHERE f.benutzername = ?
        """
        cursor.execute(sql, (nutzername,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def speichere_favorit(nutzer, s_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # SQLite kennt kein 'INSERT IGNORE', stattdessen nutzen wir 'INSERT OR IGNORE'
        sql = "INSERT OR IGNORE INTO favoriten (benutzername, spielplatz_id) VALUES (?, ?)"
        cursor.execute(sql, (nutzer, s_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"SQL-Fehler Favoriten: {e}")
        return False
    finally:
        conn.close()

# --- FUNK & NACHRICHTEN ---
def sende_nachricht(von, ziel, nachricht, is_private=False, spot_name="Allgemein"):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """INSERT INTO nachrichten (von_nutzer, recipient_id, nachricht, is_private, spot_name, gelesen) 
             VALUES (?, ?, ?, ?, ?, 0)"""
    try:
        cursor.execute(sql, (von, ziel, nachricht, int(is_private), spot_name))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei sende_nachricht: {e}")
        return False
    finally:
        conn.close()

def hole_nachrichten(user, nur_privat=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if nur_privat:
            sql = "SELECT * FROM nachrichten WHERE is_private = 1 AND (recipient_id = ? OR von_nutzer = ?) ORDER BY zeitpunkt DESC"
            cursor.execute(sql, (user, user))
        else:
            sql = "SELECT * FROM nachrichten WHERE is_private = 0 ORDER BY zeitpunkt DESC"
            cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def zaehle_ungelesene(empfaenger):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "SELECT COUNT(*) FROM nachrichten WHERE recipient_id = ? AND is_private = 1 AND gelesen = 0"
        cursor.execute(sql, (empfaenger,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except:
        return 0
    finally:
        conn.close()

def markiere_als_gelesen(empfaenger):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "UPDATE nachrichten SET gelesen = 1 WHERE recipient_id = ? AND is_private = 1"
        cursor.execute(sql, (empfaenger,))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# --- PROFIL ---
def aktualisiere_profil(user, email, vorname, nachname, alter, emoji):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = """UPDATE nutzer 
                 SET email = ?, vorname = ?, nachname = ?, alter_wert = ?, profil_emoji = ? 
                 WHERE benutzername = ?"""
        cursor.execute(sql, (email, vorname, nachname, alter, emoji, user))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei aktualisiere_profil: {e}")
        return False
    finally:
        conn.close()

# --- CREW ---
def hole_freundesliste(user):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "SELECT freund FROM freunde WHERE nutzer = ? AND status = 'bestätigt'"
        cursor.execute(sql, (user,))
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Fehler beim Laden der Crew: {e}")
        return []
    finally:
        conn.close()

def fuege_freund_hinzu(user, freund_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO freunde (nutzer, freund, status) VALUES (?, ?, 'bestätigt')"
        cursor.execute(sql, (user, freund_name))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler beim Hinzufügen zur Crew: {e}")
        return False
    finally:
        conn.close()

# BEWERTUNGEN SPEICHERN
def speichere_bewertung(s_id, nutzer, sterne, kommentar=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # SQLite kennt kein 'ON DUPLICATE KEY UPDATE'. Wir lösen das sauber mit 'INSERT OR REPLACE'
        sql = """INSERT OR REPLACE INTO bewertungen (spielplatz_id, nutzername, sterne, kommentar) 
                 VALUES (?, ?, ?, ?)"""
        cursor.execute(sql, (s_id, nutzer, sterne, kommentar))
        conn.commit()
        return True
    except Exception as e:
        print(f"SQL-Fehler Bewertung: {e}")
        return False
    finally:
        conn.close()