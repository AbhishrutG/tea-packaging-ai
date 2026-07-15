# Tea Packaging Optimization Platform — Quick Start

This is a working full-stack app: FastAPI backend (optimization engine + DB) +
Next.js frontend. Run both locally on your own machine to see and interact
with it.

## 1. Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at **http://127.0.0.1:8000**
Interactive API docs (Swagger UI, auto-generated): **http://127.0.0.1:8000/docs**

This creates a local SQLite database file (`tea_packaging.db`) automatically
on first run — no separate database setup needed for local dev.

## 2. Frontend (Next.js)

Open a **second terminal** (keep the backend running in the first one):

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**

## 3. Try it

1. Open http://localhost:3000 — you'll see an empty Dashboard first (no data yet)
2. Click "New Simulation", enter some values (defaults are pre-filled), submit
3. You'll be redirected to the results page showing the AI recommendation,
   container comparison, and current-vs-AI comparison
4. Go back to the Dashboard — it now shows real totals from your simulation

## Full documentation

See the Notion project log for detailed module-by-module explanations of
*why* each part was built the way it was — useful for the technical interview.
A full formal README (architecture, assumptions, API docs) will be added
before final submission.
