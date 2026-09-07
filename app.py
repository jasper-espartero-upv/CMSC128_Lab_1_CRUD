from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "my-secret-key"

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
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            due_date DATETIME,
            priority TEXT CHECK (priority IN ('LOW', 'MED', 'HIGH')),
            category TEXT CHECK (category IN ('School', 'Personal', 'Others')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# GET /
@app.route("/")
def index():
    conn = get_db()
    sort = request.args.get("sort")
    priority = request.args.get("priority")
    category = request.args.get("category")

    sort_options = {
        "created_at": "created_at",
        "due_date": "due_date",
        "priority": "priority",
        "category": "category"
    }

    sort_column = sort_options.get(sort)

    conditions = []
    params = []

    if priority:
        conditions.append("priority = ?")
        params.append(priority)

    if category:
        conditions.append("category = ?")
        params.append(category)

    query = "SELECT * FROM todos"

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if sort_column:
        query += " ORDER BY " + sort_column

    todos = conn.execute(query, params).fetchall()
    
    conn.close()

    return render_template(
        "index.html",
        todos=todos,
        sort=sort,
        priority=priority,
        category=category
    )

@app.route("/add", methods=["POST"])
def add():
    title = request.form["title"]
    due_date = request.form["due_date"]
    priority = request.form["priority"]
    category = request.form["category"]

    conn = get_db()
    conn.execute("INSERT INTO todos (title, due_date, priority, category) VALUES (?, ?, ?, ?)", (title, due_date, priority, category) )

    conn.commit()
    conn.close()
    flash("Task added successfully!")
    return redirect("/")

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = get_db()

    todo = conn.execute(
        "SELECT * FROM todos WHERE id = ?",
        (id,)
    ).fetchone()
    session["deleted_todo"] = dict(todo)

    conn.execute("DELETE FROM todos WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/undo", methods=["POST"])
def undo():
    todo = session.get("deleted_todo")

    if todo:
        conn = get_db()

        conn.execute(
            """INSERT INTO todos
               (id, title, completed, due_date, priority, category, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                todo["id"],
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

        session.pop("deleted_todo")

    return redirect("/")

@app.route("/clear-undo", methods=["POST"])
def clear_undo():
    session.pop("deleted_todo", None)
    return ""

@app.route("/edit/<int:id>", methods=["GET"])
def edit(id):
    conn = get_db()
    todo = conn.execute("SELECT * FROM todos WHERE id = ?", (id,)).fetchone()

    return render_template("edit.html", todo=todo)

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    title = request.form["title"]
    due_date = request.form["due_date"]
    priority = request.form["priority"]
    category = request.form["category"] 

    conn = get_db()
    conn.execute("UPDATE todos SET title = ?, due_date = ?, priority = ?, category = ?  WHERE id = ?", (title, due_date, priority, category, id))

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/status/<int:id>", methods=["POST"])
def updateCheckmark(id):
    status = request.form["status"]

    sort = request.form.get("sort", "")
    priority = request.form.get("priority", "")
    category = request.form.get("category", "")

    conn = get_db()
    conn.execute(
        "UPDATE todos SET completed = ? WHERE id = ?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect(
        f"/?sort={sort}&priority={priority}&category={category}"
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)