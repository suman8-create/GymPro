# 🏋️ GymPro — Gym Management System

A simple, beginner-friendly Gym Management System built with:
- **Flask** — Python web framework (routing, views)
- **SQLite** — Lightweight file-based database (no setup needed)
- **SQLAlchemy** — ORM to work with DB using Python objects
- **Jinja2** — HTML templating (dynamic pages)
- **Bootstrap 5** — Responsive UI via CDN

---

## 📁 Project Structure

```
gym-management/
├── app.py             ← Flask app: all routes and logic
├── models.py          ← Database models (Member + Attendance)
├── requirements.txt   ← Python dependencies
├── templates/
│   ├── base.html          ← Shared layout (navbar, flash messages)
│   ├── index.html         ← Home: list all members
│   ├── add_member.html    ← Form to add a new member
│   ├── attendance.html    ← View all attendance records
│   └── member_detail.html ← Individual member profile + history
└── static/
    ├── style.css      ← Custom dark theme styles
    └── script.js      ← Minimal JS (alert + confirm)
```

---

## 🚀 How to Run

### 1. Install Python (3.8+)
Make sure Python is installed: `python --version`

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python app.py
```

### 5. Open in browser
Visit: **http://127.0.0.1:5000**

> The SQLite database (`gym.db`) is created automatically on first run. No setup needed!

---

## 🔗 Routes

| Route                     | Method   | Description              |
|---------------------------|----------|--------------------------|
| `/`                       | GET      | Home — list all members  |
| `/add`                    | GET/POST | Add a new member         |
| `/mark_attendance/<id>`   | GET      | Mark member present today|
| `/toggle_fee/<id>`        | GET      | Toggle fee status        |
| `/attendance`             | GET      | View all attendance logs |
| `/member/<id>`            | GET      | Member detail + history  |

---

## 🗃️ Database Tables

**Member**
| Column    | Type    | Notes              |
|-----------|---------|--------------------|
| id        | Integer | Primary Key        |
| name      | String  |                    |
| phone     | String  |                    |
| join_date | Date    | Defaults to today  |
| fee_paid  | Boolean | Defaults to False  |

**Attendance**
| Column    | Type    | Notes              |
|-----------|---------|--------------------|
| id        | Integer | Primary Key        |
| member_id | Integer | FK → Member.id     |
| date      | Date    | Date of attendance |

---

## 💡 Viva Points

- **Flask** handles HTTP routes with `@app.route()`
- **SQLAlchemy** maps Python classes to DB tables (ORM)
- **Jinja2** uses `{{ }}` for variables and `{% %}` for logic
- **Relationships**: One Member → Many Attendance records (one-to-many)
- **Duplicate prevention**: Query checks if record exists before inserting
- **Bootstrap CDN**: No local files needed for styling
