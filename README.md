# CMSC 128 Lab 2

## Application Description and Implemented Features

A Flask-based user authentication and profile management system with:

* User registration and login
* Logout with confirmation popup
* Profile viewing and editing
* Password change
* Forgot password and password reset through email
* 8-character minimum password requirement

## Technology Stack

* **Frontend:** HTML, CSS, JavaScript, Jinja2
* **Backend:** Python with Flask
* **Database:** SQLite
* **Authentication:** Flask sessions and Werkzeug password hashing
* **Password Recovery:** Gmail SMTP

## Installation and Local Run

Install the required packages:

```bash
pip install flask python-dotenv
```

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
MAIL_USERNAME=yourgmail@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_FROM=yourgmail@gmail.com
RESET_BASE_URL=http://127.0.0.1:5000
```

Run the application:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000/login
```

## Database Setup

The SQLite database and required tables are automatically created when the application starts. No manual migration or seed data is required.

## Routes and Operations

| Route                     | Method    | Purpose                 |
| ------------------------- | --------- | ----------------------- |
| `/login`                  | GET, POST | Log in                  |
| `/register`               | GET, POST | Create an account       |
| `/logout`                 | POST      | Log out                 |
| `/forgot-password`        | GET, POST | Request password reset  |
| `/reset-password/<token>` | GET, POST | Reset password          |
| `/profile`                | GET, POST | View and update profile |

## Session and Password Recovery

Flask sessions store the logged-in user's ID. Protected pages check the session before allowing access.

Passwords are hashed using Werkzeug before being stored. Password reset tokens are generated securely, hashed in the database, expire after 15 minutes, and can only be used once. Reset links are sent through Gmail SMTP.
