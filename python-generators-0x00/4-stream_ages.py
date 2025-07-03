import mysql.connector

def stream_user_ages():
    """
    Generator that yields user ages one by one from the user_data table.
    """
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ALX_prodev"
    )
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT age FROM user_data")
        for row in cursor:
            age = row["age"]
            # Optionally convert from Decimal to int if needed
            if hasattr(age, "to_eng_string"):
                age = int(age)
            yield age
        cursor.close()
    finally:
        conn.close()
    return

def average_age():
    """
    Uses stream_user_ages to compute and print the average age,
    without loading the whole dataset into memory.
    """
    total = 0
    count = 0
    for age in stream_user_ages():
        total += age
        count += 1
    avg = total / count if count > 0 else 0
    print(f"Average age of users: {avg}")

if __name__ == "__main__":
    average_age()