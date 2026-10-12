# Student Management System

A web-based Student Management System developed using Python and Flask. This application helps administrators manage student records and allows students to log in and view their own details.

## Features

- Admin login
- Student login and dashboard
- Add, update, view, and delete student records
- Student account management
- Search and course summary features
- Basic chatbot integration
- SQLite database integration

## Technologies Used

- **Programming Language:** Python
- **Web Framework:** Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Version Control:** Git and GitHub

## Project Structure

```text
student management/
├── main.py
├── database.py
├── reset_admin.py
├── setup_student_account.py
├── requirements.txt
├── .gitignore
└── templates/
    ├── index.html
    ├── login.html
    ├── student_dashboard.html
    └── student_login.html
```

## How to Run the Project

1. Install Python on your computer.
2. Open the project folder in VS Code.
3. Create and activate a virtual environment (optional but recommended).
4. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the Flask application:

   ```bash
   python main.py
   ```

6. Open your browser and visit:

   `http://127.0.0.1:5000`

## Security Note

Do not upload passwords, API keys, real student data, or your local database file to a public repository.

## Author

Gagan R