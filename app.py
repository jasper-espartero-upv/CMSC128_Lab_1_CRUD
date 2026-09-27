from flask import Flask, render_template, request, redirect, session, flash
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


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

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("display_name", None)

    return redirect("/login")


# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    init_db()
    app.run(debug=True)