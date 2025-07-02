# Python MySQL Seeder: ALX_prodev Database

This project provides a Python script to **set up and populate a MySQL database** (`ALX_prodev`) with user data, using data from a CSV file. It is designed for the ALX Backend Pro Dev curriculum (Python generators project).

## Files

### `0-main.py`

- **Purpose:** The main script to run the database setup and seeding process.
- **What it does:**
  - Imports and calls functions from `seed.py`.
  - Connects to the MySQL server.
  - Creates the `ALX_prodev` database (if it doesn't exist).
  - Connects to the `ALX_prodev` database.
  - Creates the `user_data` table (if it doesn't exist).
  - Inserts data from `user_data.csv` into the table.
  - Prints out the status and displays the first 5 rows of inserted data.

### `seed.py`

- **Purpose:** Contains all utility functions to manage database connection, creation, table creation, and data insertion.
- **Key Functions:**
  - `connect_db()`: Connects to the MySQL server.
  - `create_database(connection)`: Creates the `ALX_prodev` database if it does not exist.
  - `connect_to_prodev()`: Connects to the `ALX_prodev` database.
  - `create_table(connection)`: Creates the `user_data` table if it does not exist.
  - `insert_data(connection, data)`: Inserts user data from a CSV file into the `user_data` table.
    - **Note:** If the CSV file does **not** have a `user_id` column, the script auto-generates a UUID for each user.

### `user_data.csv`

- **Purpose:** The source data for populating the database.
- **Expected Format:** The header should be:
  ```
  name,email,age
  ```
  Each row should contain a user's name, email, and age. The script will automatically generate a unique `user_id` for each row.

## Usage

1. **Ensure MySQL is running** (e.g., via XAMPP on Windows).
2. **Place `user_data.csv`** in the same directory as the scripts.
3. **Install dependencies:**
   ```sh
   pip install mysql-connector-python
   ```
4. **Run the main script:**
   ```sh
   python 0-main.py
   ```
5. **Expected Output:**
   - Confirmation messages for each step (connection, database/table creation, data insertion).
   - The first 5 rows from the database, including auto-generated user IDs.

## Notes

- This project is tested on Windows using XAMPP (default MySQL root user, no password).
- If you want to provide your own `user_id` values, add a `user_id` column as the first column in your CSV and the script will use those values.
- The table schema enforces UUID as the primary key (`user_id CHAR(36)`).

## Sample Output

```
connection successful
Database ALX_prodev created successfully
Table user_data created successfully
Data inserted successfully
Database ALX_prodev is present 
[('generated-uuid-1', 'Alice Smith', 'alice@example.com', 34), ...]
```

---