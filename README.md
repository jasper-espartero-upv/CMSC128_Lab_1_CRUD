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

## Activity 1 and Activity 2 Merge

Activity 1 and Activity 2 were merged through a pull request on the repository website. The branches were merged using the website's pull-request workflow. No merge conflicts occurred during the merge.

While reviewing the merged project, I noticed that both activities contained some common files. In those overlapping files, the Activity 2 versions replaced the Activity 1 versions. I had to manually combine parts of the two codebases to ensure that the features from both activities worked together properly.

## Database Schema and Relationships

The application uses SQLite and creates its tables automatically when it starts.

### `users`

Stores each registered account.

- `id` — primary key
- `email` — unique email address
- `display_name` — name displayed in the application
- `password` — hashed password

One user can own multiple lists and can be a member of lists owned by other users.

### `todos`

Stores tasks.

- `id` — primary key
- `title` — task title
- `completed` — completion status
- `due_date` — optional due date
- `priority` — `LOW`, `MED`, or `HIGH`
- `category` — `School`, `Personal`, or `Others`
- `created_at` — creation timestamp
- `user_id` — user who created the task
- `list_id` — list containing the task

Each task belongs to a to-do list through `list_id`. The task's `user_id` records its creator.

### `todo_lists`

Stores each user's lists.

- `id` — primary key
- `name` — list name (`Personal` or `Collaborative`)
- `owner_id` — foreign key referencing `users.id`
- `created_at` — creation timestamp

Each registered user receives a Personal list and a Collaborative list.

### `todo_list_members`

Connects users to lists they can access.

- `list_id` — foreign key referencing `todo_lists.id`
- `user_id` — foreign key referencing `users.id`
- `role` — `owner` or `member`
- Composite primary key: (`list_id`, `user_id`)

The membership table allows multiple users to access a Collaborative list. List owners are recorded as `owner`; invited users are recorded as `member`. Membership entries are removed when their associated list or user is deleted.

### `password_resets`

Stores password-reset requests.

- `id` — primary key
- `user_id` — foreign key referencing `users.id`
- `token_hash` — hash of the reset token
- `expires_at` — token expiration time
- `used` — whether the token has already been used

### Relationship summary

- **Users → Tasks:** A user can create multiple tasks; `todos.user_id` records the creator.
- **Users → Lists:** A user owns lists through `todo_lists.owner_id`.
- **Tasks → Lists:** Each task is assigned to a list through `todos.list_id`.
- **Users ↔ Lists:** `todo_list_members` implements list membership, allowing owners and invited members to access a list.
- **Users → Password resets:** A user can have password-reset records through `password_resets.user_id`.

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

## Installation and Local Run

### 1. Clone the repository

Replace `<repository-url>` with the repository's clone URL.

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```bat
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install flask python-dotenv
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=replace_with_a_long_random_secret
MAIL_USERNAME=yourgmail@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_FROM=yourgmail@gmail.com
RESET_BASE_URL=http://127.0.0.1:5000
```

The Gmail credentials and app password are used to send password-reset emails. If you do not configure email settings, the password-reset email feature will not work. Keep `.env` private and do not commit real credentials.

### 6. Run the application

```bash
python app.py
```

The SQLite database file, `todo.db`, and the required tables are initialized automatically when the application starts.

### 7. Open the application

Visit:

```text
http://127.0.0.1:5000
```

Register an account to start using the application. Each new account receives a Personal list and a Collaborative list.