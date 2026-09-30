from flask import Flask, render_template, request, redirect, session, flash
from dotenv import load_dotenv
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from email.message import EmailMessage
import sqlite3
import os
import secrets
import hashlib
import smtplib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# password reset link emailer
def send_reset_email(email, reset_link):
    message = EmailMessage()

    message["Subject"] = "Password Reset"
    message["From"] = os.getenv("MAIL_FROM")
    message["To"] = email

    message.set_content(
        f"""Hello,

You requested a password reset for your To-Do List account.

Click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you did not request a password reset, you can ignore this email.

"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(
            os.getenv("MAIL_USERNAME"),
            os.getenv("MAIL_PASSWORD")
        )
        server.send_message(message)


# ==================== DATABASE ====================

# db connector
def get_db():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn

# db generator
def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            due_date DATETIME,
            priority TEXT CHECK (priority IN ('LOW', 'MED', 'HIGH')),
            category TEXT CHECK (category IN ('School', 'Personal', 'Others')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

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

    conn.commit()
    conn.close()


# ==================== DISPLAY TASKS ====================

# GET /
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    sort = request.args.get("sort", "")
    priority = request.args.get("priority", "")
    category = request.args.get("category", "")

    sort_options = {
        "created_at": "created_at DESC",
        "due_date": "due_date ASC",
        "priority": "priority DESC",
        "category": "category ASC"
    }

    sort_column = sort_options.get(sort)

    conditions = ["user_id = ?"]
    params = [session["user_id"]]

    if priority:
        conditions.append("priority = ?")
        params.append(priority)

    if category:
        conditions.append("category = ?")
        params.append(category)

    query = "SELECT * FROM todos"

    query += " WHERE " + " AND ".join(conditions)

    if sort_column:
        query += " ORDER BY " + sort_column

    todos = conn.execute(query, params).fetchall()

    todos = [dict(todo) for todo in todos]

    for todo in todos:
        if todo["due_date"]:
            todo["due_date_display"] = datetime.strptime(
                todo["due_date"],
                "%Y-%m-%dT%H:%M"
            ).strftime("%B %d, %Y at %I:%M %p")

        if todo["created_at"]:
            todo["created_at_display"] = datetime.strptime(
                todo["created_at"],
                "%Y-%m-%d %H:%M:%S"
            ).strftime("%B %d, %Y at %I:%M %p")

    conn.close()

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
    if "user_id" not in session:
        return redirect("/login")

    title = request.form["title"]
    due_date = request.form["due_date"]
    priority = request.form["priority"]
    category = request.form["category"]

    sort = request.form.get("sort", "")
    priority_filter = request.form.get("priority_filter", "")
    category_filter = request.form.get("category_filter", "")

    conn = get_db()

    conn.execute(
        """INSERT INTO todos
        (user_id, title, due_date, priority, category)
        VALUES (?, ?, ?, ?, ?)""",
        (
            session["user_id"],
            title,
            due_date,
            priority,
            category
        )
    )

    conn.commit()
    conn.close()

    flash("Task added successfully!")

    if sort or priority_filter or category_filter:
        return redirect(
            f"/?sort={sort}&priority={priority_filter}&category={category_filter}"
        )
    
    return redirect("/")


# ==================== DELETE TASK ====================

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if "user_id" not in session:
        return redirect("/login")
    
    conn = get_db()

    sort = request.form.get("sort", "")
    priority_filter = request.form.get("priority_filter", "")
    category_filter = request.form.get("category_filter", "")

    todo = conn.execute(
        "SELECT * FROM todos WHERE id = ? AND user_id = ?",
        (id, session["user_id"])
    ).fetchone()

    if todo is None:
        conn.close()
        return redirect("/")

    session["deleted_todo"] = dict(todo)

    session["undo_sort"] = sort
    session["undo_priority"] = priority_filter
    session["undo_category"] = category_filter

    conn.execute(
        "DELETE FROM todos WHERE id = ? AND user_id = ?",
        (id, session["user_id"])
    )

    conn.commit()
    conn.close()

    if sort or priority_filter or category_filter:
        return redirect(
            f"/?sort={sort}&priority={priority_filter}&category={category_filter}"
        )

    return redirect("/")


# ==================== UNDO DELETE ====================

@app.route("/undo", methods=["POST"])
def undo():
    if "user_id" not in session:
        return redirect("/login")

    todo = session.get("deleted_todo")

    sort = session.get("undo_sort", "")
    priority_filter = session.get("undo_priority", "")
    category_filter = session.get("undo_category", "")

    if todo and todo["user_id"] == session["user_id"]:
        conn = get_db()

        conn.execute(
            """
            INSERT INTO todos
            (id, user_id, title, completed, due_date, priority, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                todo["id"],
                todo["user_id"],
                todo["title"],
                todo["completed"],
                todo["due_date"],
                todo["priority"],
                todo["category"],
                todo["created_at"]
            )
        )

        conn.commit()
        conn.close()

        session.pop("deleted_todo", None)
        session.pop("undo_sort", None)
        session.pop("undo_priority", None)
        session.pop("undo_category", None)

    if sort or priority_filter or category_filter:
        return redirect(
            f"/?sort={sort}&priority={priority_filter}&category={category_filter}"
        )

    return redirect("/")


# ==================== CLEAR UNDO ====================

@app.route("/clear-undo", methods=["POST"])
def clear_undo():
    if "user_id" not in session:
        return redirect("/login")
    
    session.pop("deleted_todo", None)
    session.pop("undo_sort", None)
    session.pop("undo_priority", None)
    session.pop("undo_category", None)

    return ""


# ==================== UPDATE TASK ====================

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    if "user_id" not in session:
        return redirect("/login")
    
    title = request.form["title"]
    due_date = request.form["due_date"]
    priority = request.form["priority"]
    category = request.form["category"] 

    sort = request.form.get("sort", "")
    priority_filter = request.form.get("priority_filter", "")
    category_filter = request.form.get("category_filter", "")

    conn = get_db()

    conn.execute(
        """UPDATE todos
        SET title = ?, due_date = ?, priority = ?, category = ?
        WHERE id = ? AND user_id = ?""",
        (
            title,
            due_date,
            priority,
            category,
            id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    flash("Task updated successfully!")

    if sort or priority_filter or category_filter:
        return redirect(
            f"/?sort={sort}&priority={priority_filter}&category={category_filter}"
        )

    return redirect("/")


# ==================== UPDATE STATUS ====================

@app.route("/status/<int:id>", methods=["POST"])
def updateCheckmark(id):
    if "user_id" not in session:
        return redirect("/login")
    
    status = request.form["status"]

    sort = request.form.get("sort", "")
    priority = request.form.get("priority", "")
    category = request.form.get("category", "")

    conn = get_db()

    conn.execute(
        """UPDATE todos
        SET completed = ?
        WHERE id = ? AND user_id = ?""",
        (
            status,
            id,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    if sort or priority or category:
        return redirect(
            f"/?sort={sort}&priority={priority}&category={category}"
        )

    return redirect("/")


# ==================== ACCOUNT ====================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["display_name"] = user["display_name"]

            return redirect("/")

        flash("Invalid email or password!")
        return redirect("/login")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"]
        display_name = request.form["display_name"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect("/register")

        password_hash = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute(
                """INSERT INTO users (email, display_name, password)
                   VALUES (?, ?, ?)""",
                (email, display_name, password_hash)
            )
            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            flash("Email already exists!")
            return redirect("/register")

        conn.close()

        flash("Account created successfully!")
        return redirect("/login")

    return render_template("register.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    session.pop("display_name", None)

    return redirect("/login")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if request.method == "POST":
        email = request.form["email"]
        display_name = request.form["display_name"]

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not email or not display_name:
            conn.close()
            flash("Email and display name are required.")
            return redirect("/profile")

        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ? AND id != ?",
            (email, session["user_id"])
        ).fetchone()

        if existing_user:
            conn.close()
            flash("That email is already being used.")
            return redirect("/profile")

        if new_password or confirm_password or current_password:

            if not current_password:
                conn.close()
                flash("Enter your current password to change your password.")
                return redirect("/profile")

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

            password_hash = generate_password_hash(new_password)

            conn.execute(
                """
                UPDATE users
                SET email = ?, display_name = ?, password = ?
                WHERE id = ?
                """,
                (
                    email,
                    display_name,
                    password_hash,
                    session["user_id"]
                )
            )

        else:
            conn.execute(
                """
                UPDATE users
                SET email = ?, display_name = ?
                WHERE id = ?
                """,
                (
                    email,
                    display_name,
                    session["user_id"]
                )
            )

        conn.commit()
        conn.close()

        session["display_name"] = display_name

        flash("Profile updated successfully!")
        return redirect("/profile")

    conn.close()

    return render_template("profile.html", user=user)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user:
            token = secrets.token_urlsafe(32)

            token_hash = hashlib.sha256(
                token.encode()
            ).hexdigest()

            expires_at = datetime.now() + timedelta(minutes=15)

            conn.execute(
                """
                UPDATE password_resets
                SET used = 1
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

            reset_link = (
                os.getenv("RESET_BASE_URL").rstrip("/")
                + "/reset-password/"
                + token
            )

            try:
                send_reset_email(
                    user["email"],
                    reset_link
                )

            except Exception:
                conn.close()

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

        conn.close()

        flash(
            "If an account with that email exists, "
            "a password reset link has been sent."
        )

    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    conn = get_db()

    reset = conn.execute(
        """
        SELECT * FROM password_resets
        WHERE token_hash = ?
        AND used = 0
        """,
        (token_hash,)
    ).fetchone()

    if reset is None:
        conn.close()
        return "Invalid or expired reset link.", 400

    expires_at = datetime.strptime(
        reset["expires_at"],
        "%Y-%m-%d %H:%M:%S"
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

        password_hash = generate_password_hash(password)

        conn.execute(
            """
            UPDATE users
            SET password = ?
            WHERE id = ?
            """,
            (
                password_hash,
                reset["user_id"]
            )
        )

        conn.execute(
            """
            UPDATE password_resets
            SET used = 1
            WHERE user_id = ?
            """,
            (reset["user_id"],)
        )

        conn.commit()
        conn.close()

        flash("Password reset successfully. You can now log in.")
        return redirect("/login")

    conn.close()

    return render_template(
        "reset_password.html",
        token=token
    )

# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)