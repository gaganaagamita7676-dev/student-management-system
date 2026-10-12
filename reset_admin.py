
from werkzeug.security import generate_password_hash
from database import connect_db

username = input("Enter admin username: ")
new_password = input("Enter new password: ")

connection = connect_db()

admin = connection.execute(
    "SELECT id FROM admins WHERE username = ?",
    (username,)
).fetchone()

if admin:
    password_hash = generate_password_hash(new_password)

    connection.execute(
        "UPDATE admins SET password_hash = ? WHERE username = ?",
        (password_hash, username)
    )

    connection.commit()
    print("Admin password reset successfully!")
else:
    print("Admin username not found.")

connection.close()
