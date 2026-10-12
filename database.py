
import sqlite3
from werkzeug.security import generate_password_hash


def connect_db():
    connection = sqlite3.connect("student.db")
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    connection = connect_db()

    try:
        # 1. Student records
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                course TEXT NOT NULL
            )
        """)

        # 2. Administrator accounts
        connection.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

        # 3. Student portal accounts
        connection.execute("""
            CREATE TABLE IF NOT EXISTS student_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                FOREIGN KEY (student_id)
                    REFERENCES students(id)
                    ON DELETE CASCADE
            )
        """)

        # 4. Create the demo admin only if it doesn't exist
        admin = connection.execute(
            "SELECT id FROM admins WHERE username = ?",
            ("admin",)
        ).fetchone()

        if admin is None:
            password_hash = generate_password_hash("Admin@123")

            connection.execute(
                """
                INSERT INTO admins (username, password_hash)
                VALUES (?, ?)
                """,
                ("admin", password_hash)
            )

        connection.commit()

    finally:
        connection.close()


create_table()
