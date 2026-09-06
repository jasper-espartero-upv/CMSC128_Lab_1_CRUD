from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


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
            category TEXT CHECK (category IN ('School', 'Personal', 'Others'))
        )
    """)

    conn.commit()
    conn.close()


# GET /
@app.route("/")
def index():
    conn = get_db()
    todos = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()

    return render_template("index.html", todos=todos)

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
    return redirect("/")

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM todos WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    return redirect("/")

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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)