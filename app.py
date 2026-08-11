from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import sqlite3, json, re, io
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
DB = BASE_DIR / "skillgap_v2.db"

# Each skill has aliases and a weight. Weights make the ATS score more realistic.
SKILLS = {
    "python": (["python", "python3"], 20),
    "django": (["django"], 12),
    "flask": (["flask"], 10),
    "fastapi": (["fastapi"], 10),
    "java": (["java"], 15),
    "spring boot": (["spring boot", "springboot"], 12),
    "javascript": (["javascript", "js"], 10),
    "typescript": (["typescript"], 8),
    "react": (["react", "reactjs", "react.js"], 10),
    "html": (["html"], 5),
    "css": (["css"], 5),
    "sql": (["sql"], 12),
    "mysql": (["mysql"], 8),
    "postgresql": (["postgresql", "postgres"], 8),
    "mongodb": (["mongodb", "mongo db"], 8),
    "sqlite": (["sqlite"], 5),
    "rest api": (["rest api", "restful api", "restful services"], 10),
    "git": (["git"], 6),
    "github": (["github"], 5),
    "docker": (["docker"], 8),
    "kubernetes": (["kubernetes", "k8s"], 8),
    "aws": (["aws", "amazon web services"], 8),
    "azure": (["azure"], 8),
    "linux": (["linux"], 5),
    "pandas": (["pandas"], 7),
    "numpy": (["numpy"], 6),
    "scikit-learn": (["scikit-learn", "sklearn"], 8),
    "machine learning": (["machine learning", "machine-learning"], 12),
    "deep learning": (["deep learning"], 10),
    "nlp": (["nlp", "natural language processing"], 10),
    "data analysis": (["data analysis", "data analytics"], 8),
    "power bi": (["power bi", "powerbi"], 6),
    "excel": (["excel", "microsoft excel"], 5),
    "oops": (["oops", "object oriented programming", "object-oriented programming"], 8),
    "selenium": (["selenium"], 7),
    "junit": (["junit"], 5),
}

ROADMAP = {
    "python": "Strengthen Python fundamentals, OOP, functions, modules and problem solving.",
    "django": "Build a Django CRUD app with models, views, templates, authentication and REST endpoints.",
    "flask": "Build a Flask REST API with validation, database integration and authentication.",
    "fastapi": "Learn FastAPI, Pydantic, dependency injection and automatic API documentation.",
    "sql": "Practice SELECT, JOIN, GROUP BY, subqueries, indexes and transactions.",
    "mysql": "Design relational schemas and practice joins, constraints, indexes and CRUD.",
    "rest api": "Learn HTTP methods, status codes, JSON, authentication and API testing.",
    "git": "Practice commits, branches, pull requests, merge conflicts and Git workflows.",
    "github": "Create polished repositories with README, issues, branches and pull requests.",
    "docker": "Containerize a Python application and connect it to a database.",
    "aws": "Learn EC2, S3, IAM and basic application deployment.",
    "react": "Learn components, props, state, hooks and API integration.",
    "pandas": "Practice DataFrames, filtering, grouping, merging and CSV analysis.",
    "machine learning": "Learn train/test split, feature engineering, model evaluation and common algorithms.",
    "nlp": "Learn text cleaning, tokenization, keyword extraction and basic text classification.",
    "data analysis": "Practice data cleaning, exploratory analysis and visualization.",
}

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate TEXT NOT NULL,
            role TEXT NOT NULL,
            score REAL NOT NULL,
            matched TEXT NOT NULL,
            missing TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

def normalize(text):
    text = text.lower().replace("c++", " cpp ")
    text = re.sub(r"[^a-z0-9+#.\- ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def contains_alias(text, alias):
    t = normalize(text)
    a = normalize(alias)
    return bool(a and re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", t))

def extract_skills(text):
    found = {}
    for skill, (aliases, weight) in SKILLS.items():
        if any(contains_alias(text, alias) for alias in aliases):
            found[skill] = weight
    return found

def extract_pdf_text(path):
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def read_resume(path):
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")

def calculate_score(job_skills, resume_skills):
    total = sum(weight for weight in job_skills.values())
    matched = {s: job_skills[s] for s in job_skills if s in resume_skills}
    earned = sum(matched.values())
    score = round((earned / total) * 100, 1) if total else 0
    return score, matched

def score_label(score):
    if score >= 85: return ("Excellent Match", "excellent")
    if score >= 70: return ("Good Match", "good")
    if score >= 50: return ("Moderate Match", "moderate")
    return ("Low Match", "low")

def save_analysis(candidate, role, score, matched, missing):
    with sqlite3.connect(DB) as conn:
        cur = conn.execute("""
        INSERT INTO analyses(candidate, role, score, matched, missing, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (candidate, role, score, json.dumps(matched), json.dumps(missing),
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return cur.lastrowid

def get_analysis(analysis_id):
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()

def make_pdf(data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 55

    c.setFont("Helvetica-Bold", 20)
    c.drawString(45, y, "Skill Gap Analysis Report")
    y -= 32

    c.setFont("Helvetica", 11)
    c.drawString(45, y, f"Candidate: {data['candidate']}")
    y -= 18
    c.drawString(45, y, f"Target Role: {data['role']}")
    y -= 18
    c.drawString(45, y, f"ATS Skill Match Score: {data['score']}%")
    y -= 30

    def section(title):
        nonlocal y
        if y < 90:
            c.showPage()
            y = height - 55
        c.setFont("Helvetica-Bold", 13)
        c.drawString(45, y, title)
        y -= 20
        c.setFont("Helvetica", 10)

    section("Matched Skills")
    for skill in data["matched"]:
        c.drawString(60, y, f"- {skill}")
        y -= 15

    y -= 8
    section("Missing Skills")
    for skill in data["missing"]:
        c.drawString(60, y, f"- {skill}")
        y -= 15

    y -= 8
    section("Learning Roadmap")
    for skill in data["missing"]:
        text = ROADMAP.get(skill, f"Learn {skill}, practice it in a project and document it on GitHub.")
        # Simple wrapping
        words = text.split()
        lines, line = [], ""
        for word in words:
            if len(line) + len(word) + 1 > 85:
                lines.append(line)
                line = word
            else:
                line = (line + " " + word).strip()
        if line: lines.append(line)

        c.setFont("Helvetica-Bold", 10)
        c.drawString(60, y, skill.title())
        y -= 14
        c.setFont("Helvetica", 10)
        for ln in lines:
            if y < 60:
                c.showPage()
                y = height - 55
            c.drawString(75, y, ln)
            y -= 13
        y -= 7

    c.save()
    buffer.seek(0)
    return buffer

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        candidate = request.form.get("candidate", "Candidate").strip() or "Candidate"
        role = request.form.get("role", "Target Role").strip() or "Target Role"
        job_text = request.form.get("job_text", "").strip()
        resume = request.files.get("resume")

        if not job_text or not resume or not resume.filename:
            flash("Please provide a resume and job description.")
            return redirect(url_for("index"))

        if resume.filename.rsplit(".", 1)[-1].lower() not in {"pdf", "txt"}:
            flash("Only PDF and TXT resumes are supported.")
            return redirect(url_for("index"))

        path = UPLOAD_FOLDER / secure_filename(resume.filename)
        resume.save(path)

        try:
            resume_text = read_resume(path)
        except Exception as e:
            flash(f"Resume reading failed: {e}")
            return redirect(url_for("index"))

        job_skills = extract_skills(job_text)
        resume_skills = extract_skills(resume_text)

        if not job_skills:
            flash("No supported technical skills were detected. Try a job description containing skills such as Python, SQL, Django, Git or REST API.")
            return redirect(url_for("index"))

        score, matched = calculate_score(job_skills, resume_skills)
        missing = {s: job_skills[s] for s in job_skills if s not in resume_skills}
        label, level = score_label(score)
        analysis_id = save_analysis(candidate, role, score, list(matched), list(missing))

        result = {
            "id": analysis_id, "candidate": candidate, "role": role,
            "score": score, "label": label, "level": level,
            "matched": sorted(matched),
            "missing": sorted(missing),
            "job_skills": sorted(job_skills),
            "resume_skills": sorted(resume_skills),
            "total": len(job_skills),
        }

    return render_template("index.html", result=result, roadmap=ROADMAP)

@app.route("/history")
def history():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT 50").fetchall()
    return render_template("history.html", rows=rows)

@app.route("/report/<int:analysis_id>")
def report(analysis_id):
    row = get_analysis(analysis_id)
    if not row:
        flash("Analysis not found.")
        return redirect(url_for("history"))

    data = {
        "candidate": row["candidate"],
        "role": row["role"],
        "score": row["score"],
        "matched": json.loads(row["matched"]),
        "missing": json.loads(row["missing"])
    }
    pdf = make_pdf(data)
    return send_file(pdf, as_attachment=True, download_name="skill_gap_report.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
