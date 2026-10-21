
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
        CREATE TABLE IF NOT EXISTS todo_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS todo_list_members (
            list_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            PRIMARY KEY (list_id, user_id),
            FOREIGN KEY (list_id) REFERENCES todo_lists(id)
                ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
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
            user_id INTEGER REFERENCES users(id),
            list_id INTEGER REFERENCES todo_lists(id)
        )
    """)

    # Give every existing user a Personal list.
    users = conn.execute("SELECT id FROM users").fetchall()

    for user in users:
        user_id = user["id"]

        personal_list = conn.execute("""
            SELECT id FROM todo_lists
            WHERE owner_id = ? AND name = 'Personal'
            LIMIT 1
        """, (user_id,)).fetchone()

        if personal_list is None:
            cursor = conn.execute("""
                INSERT INTO todo_lists (name, owner_id)
                VALUES ('Personal', ?)
            """, (user_id,))
            personal_list_id = cursor.lastrowid
        else:
            personal_list_id = personal_list["id"]

        # Give the owner access through the membership table.
        conn.execute("""
            INSERT OR IGNORE INTO todo_list_members
                (list_id, user_id, role)
            VALUES (?, ?, 'owner')
        """, (personal_list_id, user_id))

        # Keep existing tasks in their owner's Personal list.
        conn.execute("""
            UPDATE todos
            SET list_id = ?
            WHERE user_id = ? AND list_id IS NULL
        """, (personal_list_id, user_id))

        collaborative_list = conn.execute("""
            SELECT id FROM todo_lists
            WHERE owner_id = ? AND name = 'Collaborative'
            LIMIT 1
        """, (user_id,)).fetchone()

        if collaborative_list is None:
            cursor = conn.execute("""
                INSERT INTO todo_lists (name, owner_id)
                VALUES ('Collaborative', ?)
            """, (user_id,))
            collaborative_list_id = cursor.lastrowid
        else:
            collaborative_list_id = collaborative_list["id"]

        conn.execute("""
            INSERT OR IGNORE INTO todo_list_members
                (list_id, user_id, role)
            VALUES (?, ?, 'owner')
        """, (collaborative_list_id, user_id))


    conn.commit()
    conn.close()


# ==================== HELPERS ====================

def login_required():
    if "user_id" not in session:
        flash("Please log in first.")
        return False
    return True


def redirect_to_tasks():
    filters = {
        key: value
        for key, value in {
            "sort": request.form.get("sort", request.args.get("sort", "")),
            "priority": request.form.get(
                "priority_filter",
                request.form.get(
                    "priority", request.args.get("priority", "")
                )
            ),
            "category": request.form.get(
                "category_filter",
                request.form.get(
                    "category", request.args.get("category", "")
                )
            ),
            "list_id": request.form.get(
                "list_id",
                request.args.get(
                    "list_id", session.get("selected_list_id", "")
                )
            )
        }.items()
        if value
    }

    return redirect("/?" + urlencode(filters) if filters else "/")


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


def get_accessible_lists(conn, user_id):
    lists = conn.execute("""
        SELECT DISTINCT
            todo_lists.id,
            todo_lists.name,
            todo_lists.owner_id,
            users.display_name AS owner_name
        FROM todo_lists
        JOIN users ON todo_lists.owner_id = users.id
        LEFT JOIN todo_list_members
            ON todo_lists.id = todo_list_members.list_id
        WHERE todo_lists.owner_id = ?
           OR todo_list_members.user_id = ?
        ORDER BY
            CASE
                WHEN todo_lists.owner_id = ?
                     AND todo_lists.name = 'Personal'
                THEN 0
                WHEN todo_lists.owner_id = ?
                     AND todo_lists.name = 'Collaborative'
                THEN 1
                ELSE 2
            END,
            users.display_name
    """, (user_id, user_id, user_id, user_id)).fetchall()

    return lists


def get_selected_list(conn):
    user_id = session["user_id"]
    available_lists = get_accessible_lists(conn, user_id)

    requested_id = request.args.get("list_id", type=int)

    if requested_id is not None:
        for todo_list in available_lists:
            if todo_list["id"] == requested_id:
                session["selected_list_id"] = requested_id
                return todo_list

        # The requested list does not belong to or isn't shared with this user.
        session.pop("selected_list_id", None)

    # Reuse the last selected list if the user can still access it.
    saved_id = session.get("selected_list_id")

    for todo_list in available_lists:
        if todo_list["id"] == saved_id:
            return todo_list

    # Default to the first accessible list.
    if available_lists:
        session["selected_list_id"] = available_lists[0]["id"]
        return available_lists[0]

    return None


def user_can_access_list(conn, list_id, user_id):
    return conn.execute("""
        SELECT l.id
        FROM todo_lists AS l
        LEFT JOIN todo_list_members AS m
            ON m.list_id = l.id AND m.user_id = ?
        WHERE l.id = ?
          AND (l.owner_id = ? OR m.user_id IS NOT NULL)
    """, (user_id, list_id, user_id)).fetchone() is not None


def get_user_todo(conn, todo_id):
    return conn.execute("""
        SELECT t.*
        FROM todos AS t
        JOIN todo_lists AS l ON l.id = t.list_id
        LEFT JOIN todo_list_members AS m
            ON m.list_id = l.id AND m.user_id = ?
        WHERE t.id = ?
          AND (l.owner_id = ? OR m.user_id IS NOT NULL)
    """, (
        session["user_id"],
        todo_id,
        session["user_id"]
    )).fetchone()



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

    conn = get_db()

    available_lists = get_accessible_lists(conn, session["user_id"])
    requested_id = request.args.get("list_id", type=int)

    if requested_id is not None and not any(
        todo_list["id"] == requested_id for todo_list in available_lists
    ):
        previous_id = session.get("selected_list_id")

        if previous_id is not None and any(
            todo_list["id"] == previous_id for todo_list in available_lists
        ):
            flash("You can't access that list.")
            conn.close()
            return redirect(f"/?list_id={previous_id}")

    selected_list = get_selected_list(conn)

    if selected_list is None:
        conn.close()
        flash("No accessible to-do lists were found.")
        return redirect("/profile")

    conditions = ["list_id = ?"]
    params = [selected_list["id"]]

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

    todos = conn.execute(query, params).fetchall()

    # Get the members of the selected Collaborative list.
    if selected_list["name"] == "Collaborative":
        group_members = conn.execute("""
            SELECT users.display_name, todo_list_members.role
            FROM todo_list_members
            JOIN users ON todo_list_members.user_id = users.id
            WHERE todo_list_members.list_id = ?
            ORDER BY
                CASE
                    WHEN todo_list_members.role = 'owner' THEN 0
                    ELSE 1
                END,
                users.display_name
        """, (selected_list["id"],)).fetchall()
    else:
        group_members = []

    conn.close()

    todos = format_todo_dates([dict(todo) for todo in todos])
    selected_list_owner_name = selected_list["owner_name"]


    return render_template(
        "index.html",
        todos=todos,
        sort=sort,
        priority=priority,
        category=category,
        available_lists=available_lists,
        selected_list_id=selected_list["id"],
        selected_list_name=selected_list["name"],
        selected_list_owner_name=selected_list_owner_name,
        is_list_owner=(selected_list["owner_id"] == session["user_id"]),
        group_members=group_members
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
    selected_list = get_selected_list(conn)

    if selected_list is None:
        conn.close()
        flash("No accessible to-do list was found.")
        return redirect("/")

    conn.execute("""
        INSERT INTO todos
            (title, due_date, priority, category, user_id, list_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        title,
        due_date,
        priority,
        category,
        session["user_id"],
        selected_list["id"]
    ))

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
    session["undo_list_id"] = request.form.get(
    "list_id", session.get("selected_list_id", "")
    )

    conn.execute(
        "DELETE FROM todos WHERE id = ?",
        (id,)   
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

    if todo:
        conn = get_db()
        list_id = todo.get("list_id")

        # Restore only if the user still has access to the original list.
        if (
            list_id is not None
            and user_can_access_list(conn, list_id, session["user_id"])
        ):
            existing = conn.execute(
                "SELECT id FROM todos WHERE id = ?",
                (todo["id"],)
            ).fetchone()

            if not existing:
                conn.execute("""
                    INSERT INTO todos (
                        id, title, completed, due_date, priority,
                        category, created_at, user_id, list_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    todo["id"],
                    todo["title"],
                    todo["completed"],
                    todo["due_date"],
                    todo["priority"],
                    todo["category"],
                    todo["created_at"],
                    todo["user_id"],
                    list_id
                ))

                conn.commit()
                flash("Task restored successfully!")
            else:
                flash("Unable to restore the task because its ID is in use.")
        else:
            flash("You no longer have access to the original list.")

        conn.close()

    session.pop("deleted_todo", None)

    filters = {
        key: value
        for key, value in {
            "sort": session.pop("undo_sort", ""),
            "priority": session.pop("undo_priority", ""),
            "category": session.pop("undo_category", ""),
            "list_id": session.pop(
                "undo_list_id",
                session.get("selected_list_id", "")
            )
        }.items()
        if value
    }

    selected_list_id = filters.get("list_id")
    if selected_list_id:
        session["selected_list_id"] = int(selected_list_id)

    return redirect("/?" + urlencode(filters) if filters else "/")


# ==================== CLEAR UNDO ====================

@app.route("/clear-undo", methods=["POST"])
def clear_undo():
    session.pop("deleted_todo", None)
    session.pop("undo_sort", None)
    session.pop("undo_priority", None)
    session.pop("undo_category", None)
    session.pop("undo_list_id", None)
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

    conn.execute("""
        UPDATE todos
        SET title = ?, due_date = ?, priority = ?, category = ?
        WHERE id = ?
    """, (title, due_date, priority, category, id))

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
    todo = get_user_todo(conn, id)

    if todo is None:
        conn.close()
        flash("Task not found.")
        return redirect_to_tasks()

    conn.execute(
        "UPDATE todos SET completed = ? WHERE id = ?",
        (int(status), id)
    )

    conn.commit()
    conn.close()

    return redirect_to_tasks()


# ==================== INVITE COLLABORATOR ====================

@app.route("/collaborative/invite", methods=["POST"])
def invite_collaborator():
    if not login_required():
        return redirect("/login")

    email = request.form.get("email", "").strip().lower()

    if not email:
        flash("Please enter the email address of the user to invite.")
        return redirect("/")

    conn = get_db()

    # Find the current user's Collaborative list.
    collaborative_list = conn.execute("""
        SELECT id FROM todo_lists
        WHERE owner_id = ? AND name = 'Collaborative'
    """, (session["user_id"],)).fetchone()

    if collaborative_list is None:
        conn.close()
        flash("Your Collaborative list could not be found.")
        return redirect("/")

    # Find the invited account.
    invited_user = conn.execute("""
        SELECT id FROM users
        WHERE LOWER(email) = ?
    """, (email,)).fetchone()

    if invited_user is None:
        conn.close()
        flash("No account was found with that email address.")
        return redirect("/")

    if invited_user["id"] == session["user_id"]:
        conn.close()
        flash("You cannot invite yourself.")
        return redirect("/")

    # Add access only to this Collaborative list.
    cursor = conn.execute("""
        INSERT OR IGNORE INTO todo_list_members
            (list_id, user_id, role)
        VALUES (?, ?, 'member')
    """, (collaborative_list["id"], invited_user["id"]))

    conn.commit()
    already_member = cursor.rowcount == 0
    conn.close()

    if already_member:
        flash("That user already has access to your Collaborative list.")
    else:
        flash("User added to your Collaborative list successfully!")

    return redirect("/")


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
        email = request.form["email"].strip().lower()
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
        email = request.form["email"].strip().lower()
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
            cursor = conn.execute(
                """
                INSERT INTO users (email, display_name, password)
                VALUES (?, ?, ?)
                """,
                (email, display_name, password_hash)
            )

            user_id = cursor.lastrowid

            # Create the Personal list.
            cursor = conn.execute(
                """
                INSERT INTO todo_lists (name, owner_id)
                VALUES ('Personal', ?)
                """,
                (user_id,)
            )
            personal_list_id = cursor.lastrowid

            # Give the user access to their Personal list.
            conn.execute(
                """
                INSERT INTO todo_list_members (list_id, user_id, role)
                VALUES (?, ?, 'owner')
                """,
                (personal_list_id, user_id)
            )

            # Create the Collaborative list.
            cursor = conn.execute(
                """
                INSERT INTO todo_lists (name, owner_id)
                VALUES ('Collaborative', ?)
                """,
                (user_id,)
            )
            collaborative_list_id = cursor.lastrowid

            # Give the user access to their Collaborative list.
            conn.execute(
                """
                INSERT INTO todo_list_members (list_id, user_id, role)
                VALUES (?, ?, 'owner')
                """,
                (collaborative_list_id, user_id)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.rollback()
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
        email = request.form["email"].strip().lower()

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
            WHERE LOWER(email) = ? AND id != ?
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
