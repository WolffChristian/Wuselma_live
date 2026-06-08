import sqlite3
import hashlib

DB_FILE = "wuselmap.db"

# --- SYSTEM-VERBINDUNG ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_passwort(pw):
    return hashlib.sha256(str.encode(pw.strip())).hexdigest()

# --- NUTZER MANAGEMENT ---

def registriere_nutzer(un, pw, em, vn, nn, al, agb):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """INSERT INTO nutzer (benutzername, passwort, email, vorname, nachname, alter_wert, rolle) 
             VALUES (?, ?, ?, ?, ?, ?, 'user')"""
    try:
        cursor.execute(sql, (un.strip().lower(), hash_passwort(pw), em.strip(), vn, nn, al))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei registriere_nutzer: {e}")
        return False
    finally:
        conn.close()

def aktualisiere_profil(un, em, vn, nn, al, emo, pb=None):
    # 'alter_wert' an deine Tabellenstruktur angepasst
    daten = {"email": em, "vorname": vn, "nachname": nn, "alter_wert": al, "profil_emoji": emo}
    if pb is not None:
        daten["profilbild"] = pb
        
    conn = get_db_connection()
    cursor = conn.cursor()
    set_clause = ", ".join([f"`{k}`=?" for k in daten.keys()])
    values = list(daten.values()) + [un]
    try:
        cursor.execute(f"UPDATE nutzer SET {set_clause} WHERE benutzername = ?", tuple(values))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei aktualisiere_profil: {e}")
        return False
    finally:
        conn.close()

# --- MESSAGING (WUSELFUNK) ---

def sende_nachricht(von, an, text, is_private=False, spot_name='Allgemein'):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO nachrichten (von_nutzer, recipient_id, nachricht, is_private, spot_name, gelesen) VALUES (?, ?, ?, ?, ?, 0)"
    try: 
        cursor.execute(sql, (von, an, text, int(is_private), spot_name))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei sende_nachricht: {e}")
        return False
    finally:
        conn.close()

def hole_nachrichten(nutzername, nur_privat=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if nur_privat:
            sql = "SELECT * FROM nachrichten WHERE is_private = 1 AND (recipient_id = ? OR von_nutzer = ?) ORDER BY zeitpunkt DESC"
            cursor.execute(sql, (nutzername, nutzername))
        else:
            sql = "SELECT * FROM nachrichten WHERE is_private = 0 ORDER BY zeitpunkt DESC"
            cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Fehler bei hole_nachrichten: {e}")
        return []
    finally: 
        conn.close()

# --- CREW & FREUNDE ---

def fuege_freund_hinzu(nutzer, freund_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try: 
        # SQLite: 'INSERT OR IGNORE' statt 'INSERT IGNORE'
        cursor.execute("INSERT OR IGNORE INTO freunde (nutzer, freund, status) VALUES (?, ?, 'offen')", (nutzer, freund_name))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei fuege_freund_hinzu: {e}")
        return False
    finally: 
        conn.close()

def hole_freundesliste(nutzer):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT freund FROM freunde WHERE nutzer = ? AND status = 'bestätigt'", (nutzer,))
        return [row['freund'] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Fehler bei hole_freundesliste: {e}")
        return []
    finally: 
        conn.close()

def bestaetige_anfrage(absender, ich):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE freunde SET status = 'bestätigt' WHERE nutzer = ? AND freund = ?", (absender, ich))
        cursor.execute("INSERT OR IGNORE INTO freunde (nutzer, freund, status) VALUES (?, ?, 'bestätigt')", (ich, absender))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei bestaetige_anfrage: {e}")
        return False
    finally: 
        conn.close()

def lehne_anfrage_ab(absender, ich):
    conn = get_db_connection()
    cursor = conn.cursor()
    try: 
        cursor.execute("DELETE FROM freunde WHERE nutzer = ? AND freund = ?", (absender, ich))
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler bei lehne_anfrage_ab: {e}")
        return False
    finally: 
        conn.close()