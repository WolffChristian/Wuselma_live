import pymysql
import hashlib
import os
import certifi
import sys

def get_db_creds():
    return {
        "host": "gateway01.eu-central-1.prod.aws.tidbcloud.com",
        "port": 4000,
        "user": "rokiKLn3USmrdLy.root",
        "password": "JSDkSTRt28CdzRja",
        "database": "kletterdb"
    }

def get_db_connection():
    creds = get_db_creds()
    ca_path = os.path.join(sys._MEIPASS, 'certifi', 'cacert.pem') if hasattr(sys, '_MEIPASS') else certifi.where()
    try:
        return pymysql.connect(
            host=creds["host"], port=int(creds["port"]),
            user=creds["user"], password=creds["password"],
            database=creds["database"], autocommit=True, ssl={"ca": ca_path}
        )
    except Exception as e:
        print(f"❌ DB-Fehler: {e}")
        return None

def hash_passwort(pw):
    return hashlib.sha256(str.encode(pw.strip())).hexdigest()