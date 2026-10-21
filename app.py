
from flask import Flask, render_template, request, redirect, session, flash
from dotenv import load_dotenv
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from email.message import EmailMessage
from urllib.parse import urlencode
import sqlite3
import os
import secrets
import hashlib
import smtplib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# ==================== DATABASE ====================

def get_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            due_date DATETIME,
            priority TEXT CHECK (priority IN ('LOW', 'MED', 'HIGH')),
            category TEXT CHECK (
                category IN ('School', 'Personal', 'Others')
            ),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ==================== HELPERS ====================

def login_required():
    if "user_id" not in session:
        flash("Please log in first.")
        return False
    return True


def redirect_to_tasks():
    sort = request.form.get("sort", "")
    priority = request.form.get(
        "priority_filter", request.form.get("priority", "")
    )
    category = request.form.get(
        "category_filter", request.form.get("category", "")
    )

    filters = {
        key: value
        for key, value in {
            "sort": sort,
            "priority": priority,
            "category": category
        }.items()
        if value
    }

    return redirect("/?" + urlencode(filters) if filters else "/")


def get_user_todo(conn, todo_id):
    return conn.execute(
        "SELECT * FROM todos WHERE id = ? AND user_id = ?",
        (todo_id, session["user_id"])
    ).fetchone()


def format_todo_dates(todos):
    for todo in todos:
        if todo.get("due_date"):
            try:
                todo["due_date_display"] = datetime.fromisoformat(
                    todo["due_date"]
                ).strftime("%B %d, %Y at %I:%M %p")
            except ValueError:
                todo["due_date_display"] = todo["due_date"]

        if todo.get("created_at"):
            try:
                todo["created_at_display"] = datetime.fromisoformat(
                    todo["created_at"]
                ).strftime("%B %d, %Y at %I:%M %p")
            except ValueError:
                todo["created_at_display"] = todo["created_at"]

    return todos


# ==================== DISPLAY TASKS ====================

@app.route("/")
def index():
    if not login_required():
        return redirect("/login")

    sort = request.args.get("sort", "")
    priority = request.args.get("priority", "")
    category = request.args.get("category", "")

    sort_options = {
        "created_at": "created_at DESC",
        "due_date": "due_date ASC",
        "priority": "priority DESC",
        "category": "category DESC"
    }

    conditions = ["user_id = ?"]
    params = [session["user_id"]]

    if priority in ("LOW", "MED", "HIGH"):
        conditions.append("priority = ?")
        params.append(priority)

    if category in ("School", "Personal", "Others"):
        conditions.append("category = ?")
        params.append(category)

    query = "SELECT * FROM todos WHERE " + " AND ".join(conditions)

    sort_column = sort_options.get(sort)
    if sort_column:
        query += " ORDER BY " + sort_column

    conn = get_db()
    todos = conn.execute(query, params).fetchall()
    conn.close()

    todos = format_todo_dates([dict(todo) for todo in todos])

    return render_template(
        "index.html",
        todos=todos,
        sort=sort,
        priority=priority,
        category=category
    )


# ==================== ADD TASK ====================

@app.route("/add", methods=["POST"])
def add():
    if not login_required():
        return redirect("/login")

    title = request.form.get("title", "").strip()
    due_date = request.form.get("due_date", "") or None
    priority = request.form.get("priority", "")
    category = request.form.get("category", "")

    if not title:
        flash("Task title is required.")
        return redirect_to_tasks()

    if priority not in ("LOW", "MED", "HIGH"):
        flash("Please select a valid priority.")
        return redirect_to_tasks()

    if category not in ("School", "Personal", "Others"):
        flash("Please select a valid category.")
        return redirect_to_tasks()

    conn = get_db()
    conn.execute(
        """
        INSERT INTO todos (title, due_date, priority, category, user_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, due_date, priority, category, session["user_id"])
    )
    conn.commit()
    conn.close()

    flash("Task added successfully!")
    return redirect_to_tasks()


# ==================== DELETE TASK ====================

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not login_required():
        return redirect("/login")

    conn = get_db()
    todo = get_user_todo(conn, id)

    if todo is None:
        conn.close()
        flash("Task not found.")
        return redirect_to_tasks()

    session["deleted_todo"] = dict(todo)

    session["undo_sort"] = request.form.get("sort", "")
    session["undo_priority"] = request.form.get(
        "priority_filter", request.form.get("priority", "")
    )
    session["undo_category"] = request.form.get(
        "category_filter", request.form.get("category", "")
    )

    conn.execute(
        "DELETE FROM todos WHERE id = ? AND user_id = ?",
        (id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect_to_tasks()


# ==================== UNDO DELETE ====================

@app.route("/undo", methods=["POST"])
def undo():
    if not login_required():
        return redirect("/login")

    todo = session.get("deleted_todo")

    if todo and todo.get("user_id") == session["user_id"]:
        conn = get_db()

        # Restore only if the original ID is still available.
        existing = conn.execute(
            "SELECT id FROM todos WHERE id = ?",
            (todo["id"],)
        ).fetchone()

        if not existing:
            conn.execute(
                """
                INSERT INTO todos
                (id, title, completed, due_date, priority,
                 category, created_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    todo["id"],
                    todo["title"],
                    todo["completed"],
                    todo["due_date"],
                    todo["priority"],
                    todo["category"],
                    todo["created_at"],
                    session["user_id"]
                )
            )
            conn.commit()
            flash("Task restored successfully!")
        else:
            flash("Unable to restore the task because its ID is in use.")

        conn.close()

    session.pop("deleted_todo", None)
    session.pop("undo_sort", None)
    session.pop("undo_priority", None)
    session.pop("undo_category", None)

    # Restore the previous filters after undo.
    return redirect("/?" + urlencode({
        key: value for key, value in {
            "sort": session.pop("undo_sort", ""),
            "priority": session.pop("undo_priority", ""),
            "category": session.pop("undo_category", "")
        }.items() if value
    }))


# ==================== CLEAR UNDO ====================

@app.route("/clear-undo", methods=["POST"])
def clear_undo():
    session.pop("deleted_todo", None)
    session.pop("undo_sort", None)
    session.pop("undo_priority", None)
    session.pop("undo_category", None)
    return ""


# ==================== UPDATE TASK ====================

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    if not login_required():
        return redirect("/login")

    title = request.form.get("title", "").strip()
    due_date = request.form.get("due_date", "") or None
    priority = request.form.get("priority", "")
    category = request.form.get("category", "")

    if not title:
        flash("Task title is required.")
        return redirect_to_tasks()

    if priority not in ("LOW", "MED", "HIGH"):
        flash("Please select a valid priority.")
        return redirect_to_tasks()

    if category not in ("School", "Personal", "Others"):
        flash("Please select a valid category.")
        return redirect_to_tasks()

    conn = get_db()
    todo = get_user_todo(conn, id)

    if todo is None:
        conn.close()
        flash("Task not found.")
        return redirect_to_tasks()

    conn.execute(
        """
        UPDATE todos
        SET title = ?, due_date = ?, priority = ?, category = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            title, due_date, priority, category,
            id, session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    flash("Task updated successfully!")
    return redirect_to_tasks()


# ==================== UPDATE STATUS ====================

@app.route("/status/<int:id>", methods=["POST"])
def updateCheckmark(id):
    if not login_required():
        return redirect("/login")

    status = request.form.get("status", "0")
    if status not in ("0", "1"):
        flash("Invalid task status.")
        return redirect_to_tasks()

    conn = get_db()
    conn.execute(
        """
        UPDATE todos SET completed = ?
        WHERE id = ? AND user_id = ?
        """,
        (int(status), id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect_to_tasks()


# ==================== EMAIL ====================

def send_reset_email(email, reset_link):
    message = EmailMessage()
    message["Subject"] = "Password Reset"
    message["From"] = os.getenv("MAIL_FROM")
    message["To"] = email

    message.set_content(f"""Hello,

You requested a password reset for your account.

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you did not request a password reset, you can ignore this email.
""")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(
            os.getenv("MAIL_USERNAME"),
            os.getenv("MAIL_PASSWORD")
        )
        server.send_message(message)


# ==================== LOGIN ====================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        flash("You are already logged in.")
        return redirect("/profile")

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["display_name"] = user["display_name"]
            return redirect("/")

        flash("Invalid email or password!")
        return redirect("/login")

    return render_template("login.html")


# ==================== REGISTER ====================

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        flash("You are already logged in.")
        return redirect("/profile")

    if request.method == "POST":
        email = request.form["email"].strip()
        display_name = request.form["display_name"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not email or not display_name:
            flash("Email and display name are required.")
            return redirect("/register")

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect("/register")

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return redirect("/register")

        password_hash = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute(
                """
                INSERT INTO users (email, display_name, password)
                VALUES (?, ?, ?)
                """,
                (email, display_name, password_hash)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("Email already exists!")
            return redirect("/register")

        conn.close()
        flash("Account created successfully! You may now login.")
        return redirect("/login")

    return render_template("register.html")


# ==================== LOGOUT ====================

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login")


# ==================== FORGOT PASSWORD ====================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if "user_id" in session:
        flash("You are already logged in.")
        return redirect("/profile")

    if request.method == "POST":
        email = request.form["email"].strip()

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user:
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            expires_at = datetime.now() + timedelta(minutes=15)

            conn.execute(
                """
                UPDATE password_resets SET used = 1
                WHERE user_id = ? AND used = 0
                """,
                (user["id"],)
            )

            conn.execute(
                """
                INSERT INTO password_resets
                (user_id, token_hash, expires_at)
                VALUES (?, ?, ?)
                """,
                (
                    user["id"],
                    token_hash,
                    expires_at.strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            conn.commit()

            base_url = os.getenv("RESET_BASE_URL", "").rstrip("/")

            if not base_url:
                conn.close()
                app.logger.error("RESET_BASE_URL is not configured.")
                flash("Password reset is temporarily unavailable.")
                return redirect("/forgot-password")

            reset_link = f"{base_url}/reset-password/{token}"

            try:
                send_reset_email(user["email"], reset_link)
            except Exception:
                conn.execute(
                    """
                    UPDATE password_resets SET used = 1
                    WHERE user_id = ? AND token_hash = ?
                    """,
                    (user["id"], token_hash)
                )
                conn.commit()
                conn.close()

                app.logger.exception("Failed to send password reset email.")
                flash(
                    "Unable to send the password reset email. "
                    "Please try again later."
                )
                return redirect("/forgot-password")

        conn.close()

        flash(
            "If an account with that email exists, "
            "a password reset link has been sent."
        )
        return redirect("/forgot-password")

    return render_template("forgot_password.html")


# ==================== RESET PASSWORD ====================

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    conn = get_db()
    reset = conn.execute(
        """
        SELECT * FROM password_resets
        WHERE token_hash = ? AND used = 0
        """,
        (token_hash,)
    ).fetchone()

    if reset is None:
        conn.close()
        return "Invalid or expired reset link.", 400

    expires_at = datetime.strptime(
        reset["expires_at"], "%Y-%m-%d %H:%M:%S"
    )

    if datetime.now() > expires_at:
        conn.execute(
            "UPDATE password_resets SET used = 1 WHERE id = ?",
            (reset["id"],)
        )
        conn.commit()
        conn.close()
        return "This reset link has expired.", 400

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if len(password) < 8:
            conn.close()
            flash("Password must be at least 8 characters.")
            return redirect(f"/reset-password/{token}")

        if password != confirm_password:
            conn.close()
            flash("Passwords do not match.")
            return redirect(f"/reset-password/{token}")

        conn.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (
                generate_password_hash(password),
                reset["user_id"]
            )
        )

        conn.execute(
            "UPDATE password_resets SET used = 1 WHERE user_id = ?",
            (reset["user_id"],)
        )

        conn.commit()
        conn.close()

        flash("Password reset successfully. You can now log in.")
        return redirect("/login")

    conn.close()
    return render_template("reset_password.html", token=token)


# ==================== PROFILE ====================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not login_required():
        return redirect("/login")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if user is None:
        conn.close()
        session.clear()
        flash("Please log in again.")
        return redirect("/login")

    if request.method == "POST":
        email = request.form["email"].strip()
        display_name = request.form["display_name"].strip()

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not email or not display_name:
            conn.close()
            flash("Email and display name are required.")
            return redirect("/profile")

        existing_user = conn.execute(
            """
            SELECT id FROM users
            WHERE email = ? AND id != ?
            """,
            (email, session["user_id"])
        ).fetchone()

        if existing_user:
            conn.close()
            flash("That email is already being used.")
            return redirect("/profile")

        change_password = bool(
            current_password or new_password or confirm_password
        )

        if change_password:
            if not check_password_hash(user["password"], current_password):
                conn.close()
                flash("Current password is incorrect.")
                return redirect("/profile")

            if not new_password:
                conn.close()
                flash("Enter a new password.")
                return redirect("/profile")

            if len(new_password) < 8:
                conn.close()
                flash("New password must be at least 8 characters.")
                return redirect("/profile")

            if new_password != confirm_password:
                conn.close()
                flash("New passwords do not match.")
                return redirect("/profile")

            conn.execute(
                """
                UPDATE users
                SET email = ?, display_name = ?, password = ?
                WHERE id = ?
                """,
                (
                    email,
                    display_name,
                    generate_password_hash(new_password),
                    session["user_id"]
                )
            )
        else:
            conn.execute(
                """
                UPDATE users SET email = ?, display_name = ?
                WHERE id = ?
                """,
                (email, display_name, session["user_id"])
            )

        conn.commit()
        conn.close()

        session["display_name"] = display_name
        flash("Profile updated successfully!")
        return redirect("/profile")

    conn.close()
    return render_template("profile.html", user=user)


# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
