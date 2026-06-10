# 🏥 Healthcare Support Connect

> A free NGO healthcare support platform connecting underserved patients with volunteer healthcare professionals — powered by Flask, SQLite, and AI-driven health summarization.

---

## 📌 Project Overview

**Healthcare Support Connect** is a full-stack web application built for NGOs and community health initiatives. It allows patients to submit health concerns, volunteers to register their skills, and administrators to manage all submissions from a unified dashboard. An AI-powered summarizer automatically condenses each patient's health query, helping volunteers respond faster and more accurately.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🩺 Patient Support Form | Patients submit health concerns with personal details and a detailed message |
| 🤝 Volunteer Registration | Healthcare professionals register with skills and availability |
| 📬 Contact Page | General enquiries stored in the database |
| 🤖 AI Health Summarizer | Uses Claude API (with fallback rule-based NLP) to summarize each patient concern |
| 📊 Admin Dashboard | Tabular view of all patients, volunteers, and contact messages with stats |
| ✅ Form Validation | Server-side validation + client-side JS feedback |
| 💬 Flash Messages | User-friendly success/error feedback after every form submission |
| 📱 Responsive Design | Mobile-first Bootstrap 5 layout |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 · Flask 3.0 |
| Database | SQLite (via Python's built-in `sqlite3`) |
| Frontend | Bootstrap 5.3 · Bootstrap Icons · Google Fonts |
| AI Feature | Anthropic Claude API (`claude-sonnet-4-20250514`) with rule-based fallback |
| Deployment | Gunicorn · Render (or any WSGI host) |

---

## 🤖 AI Feature Description

When a patient submits a health support request, the application:

1. Sends the `health_concern` category and the patient's `message` to the **Claude API** via a direct `urllib` call (no SDK dependency required).
2. Claude returns a single-sentence, factual summary beginning with _"Patient reports…"_
3. The summary is stored in the `ai_summary` column of the `patient_requests` table.
4. The summary is displayed on the **success page** and in the **admin dashboard**.

### Fallback (No API Key Required)

If the Anthropic API is unavailable or unreachable, a built-in **rule-based summarizer** kicks in:
- Scans the message for known symptom keywords (fever, cough, pain, etc.)
- Extracts duration phrases (e.g. "3 days", "2 weeks")
- Assembles a structured summary sentence

**Example:**

> **Input:** "I have fever, headache, and body pain for the last 3 days."  
> **Output:** "Patient reports fever, headache, body pain for 3 days related to Fever & Infections."

> ⚠️ No medical diagnosis is ever made. The AI only restates the concern clearly.

---

## 🌍 NGO Use Case

Healthcare Support Connect is designed for:
- Rural health NGOs that need to triage patient concerns before connecting them with a volunteer
- Community health workers managing a large volunteer database
- Organizations that want to digitize their intake process without expensive EHR software

---

## 🗄️ Database Schema

### `patient_requests`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| full_name | TEXT | Patient's full name |
| age | INTEGER | Patient's age |
| gender | TEXT | Male / Female / Other |
| mobile | TEXT | 10-digit mobile number |
| email | TEXT | Email address |
| health_concern | TEXT | Category (dropdown) |
| message | TEXT | Detailed symptom description |
| ai_summary | TEXT | AI-generated summary |
| created_at | TEXT | ISO datetime string |

### `volunteers`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| full_name | TEXT | Volunteer's name |
| email | TEXT | Email address |
| mobile | TEXT | 10-digit mobile |
| skills | TEXT | Comma-separated skills |
| availability | TEXT | Selected availability slot |
| address | TEXT | Full address |
| created_at | TEXT | ISO datetime string |

### `contact_messages`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| name | TEXT | Sender's name |
| email | TEXT | Sender's email |
| message | TEXT | Message content |
| created_at | TEXT | ISO datetime string |

---

## 📁 Project Structure

```
healthcare-support-connect/
├── app.py                  # Flask application + routes + AI summarizer
├── database.db             # SQLite database (auto-created on first run)
├── requirements.txt        # Python dependencies
├── Procfile                # Gunicorn process declaration (Render/Heroku)
├── runtime.txt             # Python version for deployment
├── README.md               # This file
│
├── static/
│   └── style.css           # Custom CSS (healthcare-themed design)
│
└── templates/
    ├── base.html           # Master layout (navbar + footer + flash messages)
    ├── index.html          # Home page (hero + features + testimonials)
    ├── patient_form.html   # Patient support request form
    ├── volunteer_form.html # Volunteer registration form
    ├── contact.html        # Contact page + form
    ├── dashboard.html      # Admin dashboard with Bootstrap tables
    └── success.html        # Submission success page (with AI summary)
```

---

## ⚙️ Installation Steps

### Prerequisites
- Python 3.9+ installed
- `pip` available

### 1. Clone the Repository

```bash
git clone https://github.com/Ytlankadhipati/healthcare-support-connect.git
cd healthcare-support-connect
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialise the Database & Run

```bash
python app.py
```

The first run automatically creates `database.db` with all three tables.

Open your browser at: **http://127.0.0.1:5000**

---

## 🚀 Deployment on Render (Free Tier)

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit — Healthcare Support Connect"
git remote add origin https://github.com/YOUR_USERNAME/healthcare-support-connect.git
git push -u origin main
```

### Step 2 — Create a New Web Service on Render

1. Log in to [render.com](https://render.com) and click **New → Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free

### Step 3 — Add Initialisation

In Render's **Environment** tab, add:

```
SECRET_KEY=your-secure-secret-key-here
```

Then in `app.py`, update:
```python
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-dev-key')
```

### Step 4 — Deploy

Click **Create Web Service**. Render will build and deploy automatically.

> **Note on SQLite:** Render's free tier has an ephemeral filesystem — the database resets on each deploy. For production, migrate to **PostgreSQL** (Render offers a free tier) using `psycopg2` and update the DB connection in `app.py`.

---

## 📸 Screenshots

> _Add screenshots of each page after deployment:_

| Page | Screenshot |
|---|---|
| Home | `screenshots/home.png` |
| Patient Form | `screenshots/patient_form.png` |
| Volunteer Form | `screenshots/volunteer_form.png` |
| Success Page | `screenshots/success.png` |
| Dashboard | `screenshots/dashboard.png` |

---

## 🔗 GitHub Repository

```
https://github.com/Ytlankadhipati/healthcare-support-connect
```

---

## 🌐 Live Demo

```
https://healthcare-support-connect.onrender.com
```

---

## 📜 License

MIT License — free to use, modify, and distribute for NGO and community health purposes.

---

## 🙏 Acknowledgements

- [Flask](https://flask.palletsprojects.com/) — Python web framework
- [Bootstrap 5](https://getbootstrap.com/) — UI framework
- [Anthropic Claude](https://www.anthropic.com/) — AI health summarization
- [Bootstrap Icons](https://icons.getbootstrap.com/) — Icon set
- [Google Fonts](https://fonts.google.com/) — Plus Jakarta Sans · Lora
