"""
Healthcare Support Connect - Flask Application
NGO Healthcare Support Platform with AI-powered health query summarization
"""

import sqlite3
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g

# ── App Setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "hsc-secret-key-change-in-production-2024"

DATABASE = "database.db"


# ── Database Helpers ───────────────────────────────────────────────────────────
def get_db():
    """Open a database connection scoped to the current request."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # enables dict-style column access
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close DB connection at the end of every request."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables if they don't already exist."""
    with app.app_context():
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS patient_requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name   TEXT    NOT NULL,
                age         INTEGER NOT NULL,
                gender      TEXT    NOT NULL,
                mobile      TEXT    NOT NULL,
                email       TEXT    NOT NULL,
                health_concern TEXT NOT NULL,
                message     TEXT    NOT NULL,
                ai_summary  TEXT,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS volunteers (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name    TEXT NOT NULL,
                email        TEXT NOT NULL,
                mobile       TEXT NOT NULL,
                skills       TEXT NOT NULL,
                availability TEXT NOT NULL,
                address      TEXT NOT NULL,
                created_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contact_messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                email      TEXT NOT NULL,
                message    TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        db.commit()


# ── AI Summarizer ──────────────────────────────────────────────────────────────
def summarize_health_query(health_concern: str, message: str) -> str:
    """
    Generate a concise, factual summary of the patient's health concern.
    No diagnosis is made — only a plain-language restatement of the concern.
    Uses the Anthropic API via the in-app fetch capability; falls back to a
    rule-based summarizer if the API is unavailable.
    """
    try:
        import urllib.request
        import json

        prompt = (
            "You are a medical intake assistant. Summarize the following patient "
            "health concern in one clear sentence. Do NOT provide any diagnosis, "
            "medical advice, or treatment recommendation. Only restate the concern "
            "factually and concisely.\n\n"
            f"Health concern category: {health_concern}\n"
            f"Patient message: {message}\n\n"
            "Summary (one sentence, start with 'Patient reports'):"
        )

        payload = json.dumps(
            {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 120,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"].strip()

    except Exception:
        # ── Fallback rule-based summarizer ────────────────────────────────────
        return _rule_based_summary(health_concern, message)


def _rule_based_summary(health_concern: str, message: str) -> str:
    """
    Lightweight keyword-extraction summarizer used when the API is unavailable.
    Strips filler words and returns a concise summary sentence.
    """
    # Common symptom / duration keywords to surface
    symptom_keywords = [
        "fever", "cough", "pain", "headache", "fatigue", "nausea", "vomiting",
        "diarrhea", "rash", "swelling", "breathlessness", "dizziness", "weakness",
        "chest pain", "back pain", "joint pain", "anxiety", "depression", "stress",
        "diabetes", "hypertension", "cancer", "infection", "allergy", "asthma",
    ]
    duration_pattern = re.compile(
        r"\b(\d+\s*(?:day|days|week|weeks|month|months|year|years))\b", re.IGNORECASE
    )

    text = message.lower()
    found_symptoms = [kw for kw in symptom_keywords if kw in text]
    durations = duration_pattern.findall(message)

    parts = []
    if found_symptoms:
        parts.append(", ".join(found_symptoms[:4]))  # cap at 4 symptoms
    if durations:
        parts.append(f"for {durations[0]}")

    if parts:
        summary = f"Patient reports {' '.join(parts)} related to {health_concern.lower()}."
    else:
        # If nothing was extracted, produce a generic tidy sentence
        trimmed = message.strip().rstrip(".")
        # Truncate long messages
        if len(trimmed) > 120:
            trimmed = trimmed[:117] + "..."
        summary = f"Patient reports: {trimmed} (Concern: {health_concern})."

    return summary


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Home / landing page."""
    return render_template("index.html")


# ── Patient Support ────────────────────────────────────────────────────────────

@app.route("/patient", methods=["GET", "POST"])
def patient_form():
    """Patient support request form."""
    if request.method == "POST":
        full_name     = request.form.get("full_name", "").strip()
        age           = request.form.get("age", "").strip()
        gender        = request.form.get("gender", "").strip()
        mobile        = request.form.get("mobile", "").strip()
        email         = request.form.get("email", "").strip()
        health_concern = request.form.get("health_concern", "").strip()
        message       = request.form.get("message", "").strip()

        # ── Validation ──────────────────────────────────────────────────────
        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not age or not age.isdigit() or not (1 <= int(age) <= 120):
            errors.append("Please enter a valid age (1–120).")
        if not gender:
            errors.append("Please select a gender.")
        if not re.match(r"^\d{10}$", mobile):
            errors.append("Mobile number must be exactly 10 digits.")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append("Please enter a valid email address.")
        if not health_concern:
            errors.append("Please select a health concern.")
        if len(message) < 20:
            errors.append("Please describe your concern in at least 20 characters.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("patient_form.html", form_data=request.form)

        # ── AI Summary ──────────────────────────────────────────────────────
        ai_summary = summarize_health_query(health_concern, message)

        # ── Save to DB ──────────────────────────────────────────────────────
        db = get_db()
        db.execute(
            """INSERT INTO patient_requests
               (full_name, age, gender, mobile, email, health_concern, message, ai_summary, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (full_name, int(age), gender, mobile, email, health_concern, message, ai_summary,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        db.commit()

        flash("Your request has been submitted successfully!", "success")
        return render_template("success.html", name=full_name, summary=ai_summary, form_type="patient")

    return render_template("patient_form.html", form_data={})


# ── Volunteer Registration ─────────────────────────────────────────────────────

@app.route("/volunteer", methods=["GET", "POST"])
def volunteer_form():
    """Volunteer registration form."""
    if request.method == "POST":
        full_name    = request.form.get("full_name", "").strip()
        email        = request.form.get("email", "").strip()
        mobile       = request.form.get("mobile", "").strip()
        skills       = request.form.get("skills", "").strip()
        availability = request.form.get("availability", "").strip()
        address      = request.form.get("address", "").strip()

        # ── Validation ──────────────────────────────────────────────────────
        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append("Please enter a valid email address.")
        if not re.match(r"^\d{10}$", mobile):
            errors.append("Mobile number must be exactly 10 digits.")
        if not skills:
            errors.append("Please describe your skills.")
        if not availability:
            errors.append("Please select your availability.")
        if not address:
            errors.append("Address is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("volunteer_form.html", form_data=request.form)

        db = get_db()
        db.execute(
            """INSERT INTO volunteers
               (full_name, email, mobile, skills, availability, address, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (full_name, email, mobile, skills, availability, address,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        db.commit()

        flash("Thank you for registering as a volunteer!", "success")
        return render_template("success.html", name=full_name, form_type="volunteer")

    return render_template("volunteer_form.html", form_data={})


# ── Contact ────────────────────────────────────────────────────────────────────

@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page and form handler."""
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        errors = []
        if not name:
            errors.append("Name is required.")
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append("Please enter a valid email address.")
        if len(message) < 10:
            errors.append("Message must be at least 10 characters.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("contact.html", form_data=request.form)

        db = get_db()
        db.execute(
            "INSERT INTO contact_messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
            (name, email, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        db.commit()

        flash("Your message has been sent. We will get back to you shortly.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html", form_data={})


# ── Admin Dashboard ────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    """Admin dashboard — view all submissions."""
    db = get_db()
    patients   = db.execute(
        "SELECT * FROM patient_requests ORDER BY created_at DESC"
    ).fetchall()
    volunteers = db.execute(
        "SELECT * FROM volunteers ORDER BY created_at DESC"
    ).fetchall()
    contacts   = db.execute(
        "SELECT * FROM contact_messages ORDER BY created_at DESC"
    ).fetchall()
    return render_template(
        "dashboard.html",
        patients=patients,
        volunteers=volunteers,
        contacts=contacts,
    )


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
