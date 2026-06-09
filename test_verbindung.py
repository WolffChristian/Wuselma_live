from database_manager import get_db_connection

conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("Verbindung steht! Gefundene Tabellen:", tables)
    conn.close()