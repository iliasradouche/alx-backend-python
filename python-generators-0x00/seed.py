"""Module to set up and seed the ALX_prodev database.
Auto-generates user_id as UUID if missing from CSV.
"""

import mysql.connector
import csv
import uuid

def connect_db():
    """Connects to the MySQL server (not to a specific database)."""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""  # No password for XAMPP default setup
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def create_database(connection):
    """Creates the ALX_prodev database if it does not exist."""
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev;")
        cursor.close()
        print("Database ALX_prodev created successfully")
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")

def connect_to_prodev():
    """Connects to the ALX_prodev database."""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ALX_prodev"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to ALX_prodev: {err}")
        return None

def create_table(connection):
    """Creates the user_data table if it does not exist."""
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                user_id CHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                age DECIMAL NOT NULL,
                INDEX (user_id)
            );
        """)
        connection.commit()
        cursor.close()
        print("Table user_data created successfully")
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")

def insert_data(connection, data):
    """
    Inserts data from the CSV file into the user_data table.
    Auto-generates user_id as UUID for each row if not present in the CSV.
    """
    try:
        cursor = connection.cursor()
        with open(data, "r", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            # If user_id is missing in header, we generate one for each row.
            has_user_id = "user_id" in [f.lower() for f in reader.fieldnames]
            for row in reader:
                user_id = row.get("user_id") if has_user_id else str(uuid.uuid4())
                name = row["name"]
                email = row["email"]
                age = row["age"]
                cursor.execute("SELECT user_id FROM user_data WHERE user_id = %s", (user_id,))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO user_data (user_id, name, email, age) VALUES (%s, %s, %s, %s)",
                        (user_id, name, email, age)
                    )
        connection.commit()
        cursor.close()
        print("Data inserted successfully")
    except Exception as err:
        print(f"Error inserting data: {err}")