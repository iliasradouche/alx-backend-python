import mysql.connector

def stream_users():
    """
    Yields all users from the user_data table, one by one, as dictionaries.
    No server-side cursor, so no 'unread result' error.
    Only one loop is used.
    """
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ALX_prodev"
    )
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_data")
        rows = cursor.fetchall()
        for row in rows:
            # Optionally convert Decimal to int for pretty output:
            if "age" in row and hasattr(row["age"], "to_eng_string"):
                row["age"] = int(row["age"])
            yield row
        cursor.close()
    finally:
        conn.close()