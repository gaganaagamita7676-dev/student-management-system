
import os
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from werkzeug.security import check_password_hash
from database import connect_db

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-deployment"
)


# ---------------- ADMIN LOGIN PROTECTION ----------------

def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in as an administrator.")
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)
    return wrapped_view


# ---------------- STUDENT LOGIN PROTECTION ----------------

def student_login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "student_account_id" not in session:
            flash("Please log in to your student account.")
            return redirect(url_for("student_login"))
        return view_function(*args, **kwargs)
    return wrapped_view


# ---------------- HOME PAGE ----------------

@app.route("/")
def index():
    if "admin_id" in session:
        return redirect(url_for("home"))
    if "student_account_id" in session:
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("login"))


# ---------------- ADMIN LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "admin_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = connect_db()
        try:
            admin = connection.execute(
                """
                SELECT id, username, password_hash
                FROM admins
                WHERE username = ?
                """,
                (username,)
            ).fetchone()
        finally:
            connection.close()

        if admin and check_password_hash(
            admin["password_hash"], password
        ):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("home"))

        flash("Invalid administrator username or password.")

    return render_template("login.html")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def home():
    search = request.args.get("search", "").strip()

    connection = connect_db()
    try:
        total_students = connection.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        course_summary = connection.execute(
            """
            SELECT course, COUNT(*) AS total
            FROM students
            GROUP BY course
            ORDER BY course
            """
        ).fetchall()

        if search:
            students = connection.execute(
                """
                SELECT id, name, age, course
                FROM students
                WHERE name LIKE ?
                   OR course LIKE ?
                   OR CAST(id AS TEXT) LIKE ?
                ORDER BY id DESC
                """,
                (
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%"
                )
            ).fetchall()
        else:
            students = connection.execute(
                """
                SELECT id, name, age, course
                FROM students
                ORDER BY id DESC
                """
            ).fetchall()
    finally:
        connection.close()

    return render_template(
        "index.html",
        students=students,
        total_students=total_students,
        course_summary=course_summary,
        search=search,
        admin_username=session.get("admin_username", "Admin")
    )


# ---------------- ADD STUDENT ----------------

@app.route("/add", methods=["POST"])
@login_required
def add_student():
    name = request.form.get("name", "").strip()
    age_text = request.form.get("age", "").strip()
    course = request.form.get("course", "").strip()

    if not name or not age_text or not course:
        flash("Please fill in all student fields.")
        return redirect(url_for("home"))

    try:
        age = int(age_text)
        if age < 1 or age > 120:
            raise ValueError
    except ValueError:
        flash("Please enter a valid age.")
        return redirect(url_for("home"))

    connection = connect_db()
    try:
        connection.execute(
            """
            INSERT INTO students (name, age, course)
            VALUES (?, ?, ?)
            """,
            (name, age, course)
        )
        connection.commit()
        flash("Student added successfully.")
    finally:
        connection.close()

    return redirect(url_for("home"))


# ---------------- UPDATE STUDENT ----------------

@app.route("/update/<int:student_id>", methods=["POST"])
@login_required
def update_student(student_id):
    name = request.form.get("name", "").strip()
    age_text = request.form.get("age", "").strip()
    course = request.form.get("course", "").strip()

    if not name or not age_text or not course:
        flash("Please fill in all student fields.")
        return redirect(url_for("home"))

    try:
        age = int(age_text)
        if age < 1 or age > 120:
            raise ValueError
    except ValueError:
        flash("Please enter a valid age.")
        return redirect(url_for("home"))

    connection = connect_db()
    try:
        result = connection.execute(
            """
            UPDATE students
            SET name = ?, age = ?, course = ?
            WHERE id = ?
            """,
            (name, age, course, student_id)
        )
        connection.commit()

        if result.rowcount:
            flash("Student details updated successfully.")
        else:
            flash("Student record not found.")
    finally:
        connection.close()

    return redirect(url_for("home"))


# ---------------- DELETE STUDENT ----------------

@app.route("/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    connection = connect_db()
    try:
        connection.execute(
            "DELETE FROM student_accounts WHERE student_id = ?",
            (student_id,)
        )

        result = connection.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )
        connection.commit()

        if result.rowcount:
            flash("Student deleted successfully.")
        else:
            flash("Student record not found.")
    finally:
        connection.close()

    return redirect(url_for("home"))


# ---------------- ADMIN LOGOUT ----------------

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have logged out successfully.")
    return redirect(url_for("login"))


# ---------------- STUDENT LOGIN ----------------

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if "student_account_id" in session:
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        student_id_text = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")

        try:
            student_id = int(student_id_text)
            if student_id < 1:
                raise ValueError
        except ValueError:
            flash("Please enter a valid Student ID.")
            return render_template("student_login.html")

        connection = connect_db()
        try:
            account = connection.execute(
                """
                SELECT sa.id AS account_id,
                       sa.student_id,
                       sa.password_hash,
                       s.name
                FROM student_accounts AS sa
                JOIN students AS s ON s.id = sa.student_id
                WHERE sa.student_id = ?
                """,
                (student_id,)
            ).fetchone()
        finally:
            connection.close()

        if account and check_password_hash(
            account["password_hash"], password
        ):
            session.clear()
            session["student_account_id"] = account["account_id"]
            session["student_id"] = account["student_id"]
            session["student_name"] = account["name"]
            return redirect(url_for("student_dashboard"))

        flash("Invalid Student ID or password.")

    return render_template("student_login.html")


# ---------------- STUDENT DASHBOARD ----------------

@app.route("/student/dashboard")
@student_login_required
def student_dashboard():
    connection = connect_db()
    try:
        student = connection.execute(
            """
            SELECT id, name, age, course
            FROM students
            WHERE id = ?
            """,
            (session["student_id"],)
        ).fetchone()
    finally:
        connection.close()

    if student is None:
        session.clear()
        flash("Student record not found. Contact the administrator.")
        return redirect(url_for("student_login"))

    return render_template(
        "student_dashboard.html",
        student=student
    )


# ---------------- STUDENT LOGOUT ----------------

@app.route("/student/logout", methods=["POST"])
def student_logout():
    session.clear()
    flash("You have logged out successfully.")
    return redirect(url_for("student_login"))


# ---------------- LOCAL CHATBOT ----------------

def get_basic_chatbot_answer(message):
    text = message.lower().strip()

    if any(word in text for word in ["hello", "hi", "hey"]):
        return (
            "Hello, Administrator! How can I help you today?"
        )

    if "help" in text:
        return (
            "I can help with student totals, courses, searching "
            "student records, and using the dashboard."
        )

    if "how many students" in text or "student count" in text:
        return "__STUDENT_COUNT__"

    if "course" in text or "courses" in text:
        return "__COURSE_LIST__"

    if "find student" in text or "search student" in text:
        return (
            "Use the search box to search by student ID, name, or course."
        )

    if "dashboard" in text:
        return (
            "The administrator dashboard lets you view, add, search, "
            "update, and delete student records."
        )

    if "student portal" in text or "my details" in text:
        return (
            "Students log in with their Student ID and password "
            "to view their own details."
        )

    return (
        "I can answer basic questions about student totals, courses, "
        "searching records, and the student portal. For broader "
        "AI-generated responses, configure an OpenAI API key."
    )


# ---------------- OPTIONAL OPENAI AI ----------------

def get_ai_answer(message):
    # Always answer database questions using actual database data.
    basic_answer = get_basic_chatbot_answer(message)

    if basic_answer in ("__STUDENT_COUNT__", "__COURSE_LIST__"):
        return basic_answer

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return basic_answer

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions=(
                "You are an assistant for a college student management "
                "system. Use simple English. Do not reveal passwords, "
                "secret keys, or private student records. Do not claim "
                "to know database facts unless supplied."
            ),
            input=message
        )

        return response.output_text.strip() or basic_answer

    except Exception:
        app.logger.exception("AI chatbot request failed.")
        return (
            "The AI service is unavailable right now. Please try again."
        )


# ---------------- CHATBOT API ----------------

@app.route("/chatbot", methods=["POST"])
@login_required
def chatbot():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"reply": "Please type a question."}), 400

    if len(message) > 1000:
        return jsonify({
            "reply": "Please keep your question under 1000 characters."
        }), 400

    answer = get_ai_answer(message)

    if answer == "__STUDENT_COUNT__":
        connection = connect_db()
        try:
            total = connection.execute(
                "SELECT COUNT(*) FROM students"
            ).fetchone()[0]
        finally:
            connection.close()

        answer = f"There are currently {total} student records."

    elif answer == "__COURSE_LIST__":
        connection = connect_db()
        try:
            rows = connection.execute(
                """
                SELECT DISTINCT course
                FROM students
                ORDER BY course
                """
            ).fetchall()
        finally:
            connection.close()

        courses = [row["course"] for row in rows]
        answer = (
            "Available courses: " + ", ".join(courses) + "."
            if courses
            else "No courses have been added yet."
        )

    return jsonify({"reply": answer})


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)
