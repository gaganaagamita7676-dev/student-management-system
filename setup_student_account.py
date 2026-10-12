
from getpass import getpass
from werkzeug.security import generate_password_hash
from database import connect_db


def create_student_account():
    try:
        student_id = int(input("Enter existing Student ID: "))
        if student_id < 1:
            raise ValueError
    except ValueError:
        print("Please enter a valid Student ID.")
        return

    password = getpass("Create password (minimum 8 characters): ")
    confirm_password = getpass("Confirm password: ")

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    connection = connect_db()

    try:
        student = connection.execute(
            "SELECT id, name FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()

        if student is None:
            print("Student not found. Add the student through the Admin Portal first.")
            return

        password_hash = generate_password_hash(password)

        connection.execute(
            """
            INSERT INTO student_accounts (student_id, password_hash)
            VALUES (?, ?)
            ON CONFLICT(student_id)
            DO UPDATE SET password_hash = excluded.password_hash
            """,
            (student_id, password_hash)
        )

        connection.commit()
        print(f"Account created successfully for {student['name']}!")

    except Exception as error:
        connection.rollback()
        print("Error:", error)

    finally:
        connection.close()


if __name__ == "__main__":
    create_student_account()
