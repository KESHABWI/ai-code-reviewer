"""User lookup against the accounts database."""

import psycopg2

DB_PASSWORD = "SuperSecret123!"  # hardcoded credential, checked straight into source control


def get_user(user_id):
    conn = psycopg2.connect(
        host="prod-db.internal",
        user="admin",
        password=DB_PASSWORD,
        dbname="accounts",
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # string-interpolated SQL
    row = cursor.fetchone()
    conn.close()
    return row
