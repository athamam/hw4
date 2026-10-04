# Campus Customs (MGT 409 · HW4)

A customer storefront for **Campus Customs** — officially licensed Yale apparel — with an
AI shopping assistant. React + Vite + TypeScript front end, FastAPI back end, and a
**PydanticAI** agent (`gpt-5.6-luna` via the Portkey gateway) that searches the catalogue,
checks stock, remembers logged-in customers, and shows product cards on the page.

## Layout

```
hw4/
├── AI_prompts.md          # log of prompts used to build this (Problem 1)
├── requirements.txt       # Python backend dependencies
├── .env.example           # copy to .env and add your key
├── .gitignore
├── README.md
├── frontend/              # Vite + React + TypeScript app
├── backend/               # FastAPI app (run with uvicorn)
│   ├── main.py            # API: products, auth, images, /api/chat
│   ├── agent.py           # builds + runs the PydanticAI agent   ┐
│   ├── tools.py           # agent tools (catalogue / stock)      │ the agent
│   ├── models.py          # Pydantic models + deps               │ is these
│   ├── prompts/prompt.md  # agent instructions (voice + safety)  ┘ four files
│   ├── auth.py, db.py, routes_auth.py, memory.py, audit.py   # supporting modules
└── output/               # harness.md, design.md, usability.md, app_check.html, audit_trail.json
```

### Local-only data pack (not in git)

The database and product images are **not** committed. Before running, place the provided
data pack so the layout is:

```
hw4/
└── data/
    ├── campus_customs.db     # catalogue, inventory, users, chat history
    └── products/             # product images referenced by the catalogue
```

## Setup

### 1. API key
Copy `.env.example` to `.env` **in this `hw4/` folder** and add your Portkey key:

```
PORTKEY_API_KEY=your-portkey-api-key-here
```

### 2. Backend (FastAPI, port 8000)
From the `hw4/` folder:

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (PowerShell/Git Bash)
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Then run from the `backend/` folder:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 3. Frontend (Vite + React, port 5173)
In a second terminal, from the `frontend/` folder:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` and `/images` to the backend at
`:8000`, so start the backend first.

## Using the site
- **Browse** products, search/filter/sort on the Products page, open a product for full
  details and per-size stock.
- **Create an account / log in** (passwords are hashed with PBKDF2; never stored plaintext).
  A seed test account exists: `test@campuscustoms.yale.edu` / `password`.
- **Chat** via the bottom-right bubble: ask for gear ("show me hoodies under $60"), check
  stock, or, on a product page, "do you have this in pink?". Matches appear as cards on the
  page. Logged-in users' chat history is saved and reloaded on return; guests can chat too.

## Notes for graders
- Every agent run is appended to `output/audit_trail.json` (append-only).
- `output/harness.md` documents the data model, tools, safety rules, and specs.
- The agent's behavior and safety rules live in `backend/prompts/prompt.md`.
