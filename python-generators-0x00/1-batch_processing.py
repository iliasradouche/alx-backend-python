import mysql.connector

def stream_users_in_batches(batch_size):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ALX_prodev"
    )
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_data")
        batch = []
        for row in cursor:
            if "age" in row and hasattr(row["age"], "to_eng_string"):
                row["age"] = int(row["age"])
            batch.append(row)
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
        cursor.close()
    finally:
        conn.close()
    return  

def batch_processing(batch_size):
    for batch in stream_users_in_batches(batch_size):
        for user in batch:
            if user.get("age", 0) > 25:
                print(user)
    return  