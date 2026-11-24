# To-Do List Web Application

## Application Description and Features

A Flask-based to-do list application that supports user accounts, task management, and collaborative lists.

- User registration, login, and logout
- Profile viewing and editing, including password changes
- Forgot-password and password-reset flow through email
- Create, view, edit, delete, and complete tasks
- Sort and filter tasks by due date, priority, and category
- Undo task deletion
- Separate Personal and Collaborative lists for each user
- Invite existing users to a Collaborative list
- View the members of a Collaborative list
- Restrict list and task access based on ownership or list membership

## Technology Stack

- **Frontend:** HTML, CSS, JavaScript, Jinja2
- **Backend:** Python with Flask
- **Database:** SQLite
- **Authentication:** Flask sessions and Werkzeug password hashing
- **Password recovery:** Gmail SMTP
- **Deployment:** PythonAnywhere

### Backend Refactoring and Optimization

The backend was refactored to reduce unnecessary queries and improve code organization.

- Reused the already retrieved list data when determining the selected list instead of querying the database again.
- Reused the logged-in user's display name from the session instead of retrieving it from the database again.
- Reused the accessible list data in multiple parts of the request instead of fetching it repeatedly.
- Removed unnecessary repeated database lookups where existing data could already be reused.

These changes reduce redundant database operations while keeping the existing functionality and access-control rules intact.

## Routes and Operations

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Display tasks in the selected accessible list; supports sorting and filtering |
| POST | `/add` | Add a task to the selected accessible list |
| POST | `/update/<id>` | Update a task after checking that the current user can access its list |
| POST | `/delete/<id>` | Delete a task after checking that the current user can access its list |
| POST | `/status/<id>` | Change a task's completion status after checking access |
| POST | `/undo` | Restore a deleted task only if the user still has access to its original list |
| POST | `/collaborative/invite` | Invite an existing account to the current user's Collaborative list |
| GET, POST | `/login` | Authenticate an account and create a session |
| GET, POST | `/register` | Register an account and create its Personal and Collaborative lists |
| POST | `/logout` | Clear the current session |
| GET, POST | `/profile` | View or update the current user's profile |
| GET, POST | `/forgot-password` | Request a password-reset email |
| GET, POST | `/reset-password/<token>` | Validate a reset token and update the password |

## Ownership and Access Checks

- **List access:** `user_can_access_list(conn, list_id, user_id)` checks whether the current user owns a list or appears in `todo_list_members`.
- **Task access:** `get_user_todo(conn, todo_id)` joins tasks to their lists and checks whether the current user owns the list or is a member of it. Update, delete, and completion-status routes use this helper before changing a task.
- **Selected list:** The home route loads only lists returned by `get_accessible_lists()`. A requested list ID that the user cannot access is rejected.
- **Inviting collaborators:** `/collaborative/invite` looks up the current user's own Collaborative list using `owner_id = session["user_id"]`. It adds the invited account to that list only; it does not grant access to the inviter's Personal list.
- **Authentication:** Protected routes check for a logged-in `user_id` in the Flask session.

For example, when a user submits `POST /update/12`, the server calls `get_user_todo(conn, 12)`. If task 12 is not in a list that the current user owns or can access as a member, the helper returns no task and the update is refused.

## Local Setup

### Requirements

- Python 3
- Git

### 1. Clone the repository

```bash
git clone https://github.com/jasper-espartero-upv/CMSC128_Lab_1_CRUD
cd CMSC128_Lab_1_CRUD
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=replace_with_a_long_random_secret
MAIL_USERNAME=yourgmail@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_FROM=yourgmail@gmail.com
RESET_BASE_URL=http://127.0.0.1:5000
```

- `SECRET_KEY` is used to secure Flask sessions.
- `MAIL_USERNAME` is the Gmail account used to send password-reset emails.
- `MAIL_PASSWORD` is the Gmail App Password for that account.
- `MAIL_FROM` is the email address shown as the sender.
- `RESET_BASE_URL` is the base URL used when generating password-reset links locally.

### 5. Run the application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

## Deployed Application

The application is deployed using PythonAnywhere.

**Live application:**

https://jasper0.pythonanywhere.com

No additional setup is required. The application can be accessed directly through a web browser.
