# AI Olympiad Prep

Local study app for USA-NA-AIO practice. Navigation is **Learn**, **Practice**, and **Settings**.

Unofficial practice material — not official contest questions.

## Run

```powershell
cd backend
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL (often http://localhost:5175). Sign up, then use Learn / Practice.

## Learn

Khan Academy-style modules: short lessons with quick checks between them.

## Practice

Pick topic, optional subtopic, and difficulty (easy / medium / hard).

Each subtopic has **50 easy**, **100 medium**, and **50 hard** questions (21,600 total across 108 subtopics).

## Auth

Email/password signup. Google OAuth when you add keys to `backend/.env`:

```dotenv
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:5175
```
