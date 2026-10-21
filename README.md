# CMSC 128 Lab 2

## Application Description and Implemented Features

A Flask-based user authentication and profile management system with:

* User registration and login
* Logout with confirmation popup
* Profile viewing and editing
* Password change
* Forgot password and password reset through email

## Technology Stack

* **Frontend:** HTML, CSS, JavaScript, Jinja2
* **Backend:** Python with Flask
* **Database:** SQLite
* **Authentication:** Flask sessions and Werkzeug password hashing
* **Password Recovery:** Gmail SMTP

## Installation and Local Run

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Create a virtual environment

**Windows PowerShell:**

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```bash
.\venv\Scripts\Activate.ps1
```


### 4. Install the required packages

```bash
pip install flask python-dotenv
```

### 5. Create the `.env` file

Create a `.env` file in the project root directory:

```env
SECRET_KEY=your_secret_key
MAIL_USERNAME=yourgmail@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_FROM=yourgmail@gmail.com
RESET_BASE_URL=http://127.0.0.1:5000
```

The Gmail account and app password are used to send password reset emails.

### 6. Run the application

Make sure the virtual environment is still activated:

```bash
python app.py
```

### 7. Open the application

Open the following URL in a browser:

```text
http://127.0.0.1:5000/login
```

## Database Setup

The SQLite database and required tables are automatically created when the application starts. No manual migration or seed data is required.

## Routes and Operations

| Method    | Endpoint                  | Description                        |
| --------- | ------------------------- | ---------------------------------- |
| GET, POST | `/login`                  | Log in to an account               |
| GET, POST | `/register`               | Create a new account               |
| POST      | `/logout`                 | Log out of the current account     |
| GET, POST | `/forgot-password`        | Request a password reset           |
| GET, POST | `/reset-password/<token>` | Reset the account password         |
| GET, POST | `/profile`                | View and update the user's profile |

## Session and Password Recovery

Flask sessions store the logged-in user's ID. Protected pages check the session before allowing access.

Passwords are hashed using Werkzeug before being stored. Password reset tokens are generated securely, hashed in the database, expire after 15 minutes, and can only be used once. Reset links are sent through Gmail SMTP.
