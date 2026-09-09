# To-Do List App

A simple To-Do List web application that allows users to add, view, edit, delete, and mark tasks as completed. It also includes task sorting, filtering, and undo delete functionality.

## Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python with Flask
* **Database:** SQLite

### Why These Technologies?

**Flask** was chosen for the backend because it is lightweight, simple to set up, and provides the routing and request handling needed for a CRUD application.

**SQLite** was chosen because it is a lightweight database that does not require a separate database server. It is suitable for a small application and allows tasks to persist even after the application is restarted.

**HTML, CSS, and JavaScript** were used for the frontend because they provide the basic structure, styling, and interactive features of the application.

## How to Run Locally

### 1. Clone the repository

```bash
git clone <repository-url>
cd CMSC128_Lab_1_CRUD
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install flask python-dotenv
```

### 5. Set up the environment variable

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
```

### 6. Run the application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

The SQLite database (`todo.db`) is created automatically when the application is started.

## CRUD Operations / API Endpoints

The application uses Flask routes to handle CRUD operations.

| Method | Endpoint       | Description                                      |
| ------ | -------------- | ------------------------------------------------ |
| GET    | `/`            | Displays all tasks and handles sorting/filtering |
| POST   | `/add`         | Adds a new task                                  |
| POST   | `/update/<id>` | Updates an existing task                         |
| POST   | `/delete/<id>` | Deletes a task                                   |
| POST   | `/undo`        | Restores the most recently deleted task          |
| POST   | `/status/<id>` | Marks a task as completed or incomplete          |
| POST   | `/clear-undo`  | Clears the stored undo task                      |