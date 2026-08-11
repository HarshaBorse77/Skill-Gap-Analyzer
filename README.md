# Skill Gap Analyzer V2

A resume-to-job skill gap analyzer built with Python and Flask.

## V2 Features

- PDF/TXT resume parsing
- Rule-based NLP-style skill extraction with aliases
- Weighted ATS skill score
- Matched and missing skills
- Visual dashboard
- Personalized learning roadmap
- SQLite analysis history
- Downloadable PDF report
- Responsive UI

## Project structure

skill_gap_analyzer_v2/
- app.py
- requirements.txt
- README.md
- templates/index.html
- templates/history.html
- static/style.css
- uploads/

## Run on Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Run on macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## How V2 calculates the ATS score

Every detected job skill has a weight. Example:

Python = 20
Django = 12
SQL = 12
Git = 6

Score = sum(weights of matched skills) / sum(weights of all detected job skills) * 100

This is an educational ATS prototype. Real ATS systems use much more sophisticated parsing, ranking and semantic matching.

## How to demonstrate it

1. Put Python, SQL and Git in your sample resume.
2. Paste a Python Developer job description containing Python, Django, SQL, Git, Docker and AWS.
3. Run analysis.
4. Show the weighted score.
5. Explain why Django, Docker and AWS are gaps.
6. Download the PDF report.
7. Open Analysis History.

## Strong V3 upgrades

- User registration/login
- DOCX resume support
- spaCy/transformer semantic matching
- Job-role skill database
- Admin dashboard
- Resume section scoring
- Email report
- Docker deployment
- Cloud deployment
