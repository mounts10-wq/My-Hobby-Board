# MyHobbyBoard

MyHobbyBoard is a full-stack web application built for hobbyists, makers, and builders to track project ideas, manage tasks, and document milestone progress with media and community updates.

Website: [https://myhobbyboard.com](https://myhobbyboard.com)

## Features

- **Authentication & Security:** JWT authentication with password hashing, secure token storage, and ownership-based authorization.
- **Project & Task Management:** Full CRUD project workspaces with material checklists, notes, status tracking, and priority tagging.
- **Progress Tracking & Visuals:** Live dashboard analytics, milestone updates with photo and video uploads.
- **AI Planning Assistant:** Intelligent project milestone and prep recommendations powered by Google Gemini (with resilient built-in fallbacks).
- **Social Discovery & Follows:** Public project discovery, granular board-level follows, milestone feeds, and update comments.
- **Production Architecture:** Decoupled React frontend (Vite) and Flask backend (Gunicorn + PostgreSQL support).

## Tech Stack

Frontend:
- React 19
- React Router 7
- Vite 8
- CSS3 (custom design system)

Backend:
- Python 3.12+
- Flask & Gunicorn
- Flask-SQLAlchemy (SQLite for local dev / PostgreSQL for production)
- Flask-Migrate & Alembic
- Flask-JWT-Extended
- Flask-CORS
- Google Gemini AI REST API (with Anthropic fallback)

## API Summary

All backend endpoints are under `/api`.

Utility:
- `GET /api/health`
- `GET /api/dashboard/stats` (protected)

Auth:
- `POST /api/signup`
- `POST /api/login`
- `GET /api/me`
- `POST /api/logout`

Boards:
- `GET /api/boards?page=1&per_page=10`
- `POST /api/boards`
- `GET /api/boards/:id`
- `PATCH /api/boards/:id`
- `DELETE /api/boards/:id`

Tasks:
- `GET /api/boards/:board_id/tasks?page=1&per_page=10`
- `POST /api/boards/:board_id/tasks`
- `GET /api/tasks/:id`
- `PATCH /api/tasks/:id`
- `DELETE /api/tasks/:id`

Board Updates & Media:
- `GET /api/boards/:board_id/updates`
- `POST /api/boards/:board_id/updates`
- `DELETE /api/updates/:id`
- `GET /api/uploads/:filename` (protected token download)

Assistant:
- `POST /api/assistant/plan`

Comments:
- `GET /api/updates/:update_id/comments`
- `POST /api/updates/:update_id/comments`

Social:
- `GET /api/feed`
- `GET /api/discover/boards`
- `GET /api/me/following`
- `GET /api/me/following/boards`
- `POST /api/users/:target_user_id/follow`
- `DELETE /api/users/:target_user_id/follow`
- `POST /api/boards/:board_id/follow`
- `DELETE /api/boards/:board_id/follow`

## Local Development

### 1. Backend Setup

```bash
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Start the backend:

```bash
python3 run.py
```

Runs at: `http://127.0.0.1:5000`

### 2. Frontend Setup

Open a second terminal:

```bash
cd client
npm install
cp .env.example .env
npm run dev
```

Runs at: `http://127.0.0.1:5173`

### 3. Running Verification Tests

Backend tests:
```bash
cd server
source venv/bin/activate
pytest -q tests
```

Frontend lint & build:
```bash
cd client
npm run lint
npm run build
```

## Deployment Guide (Render & Custom Domain)

### Backend Deployment (Render Web Service)
1. Push repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), create a **New Web Service**:
   - **Root Directory:** `server`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app`
3. Add Environment Variables:
   - `SECRET_KEY`: (generate random 32+ char string)
   - `JWT_SECRET_KEY`: (generate random 32+ char string)
   - `DATABASE_URL`: (PostgreSQL database internal URL or SQLite default)
   - `GEMINI_API_KEY`: (free key from Google AI Studio)
   - `CORS_ORIGINS`: `https://myhobbyboard.com,https://www.myhobbyboard.com`

### Frontend Deployment (Render Static Site / Vercel)
1. In Render (Static Site) or Vercel:
   - **Root Directory:** `client`
   - **Build Command:** `npm run build`
   - **Publish Directory:** `dist`
2. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://api.myhobbyboard.com/api` (or your Render backend URL e.g. `https://myhobbyboard-api.onrender.com/api`)

### Custom Domain Setup (MyHobbyBoard.com)
1. In your domain registrar DNS settings (Namecheap, Cloudflare, Google Domains, etc.):
   - Add **CNAME** or **A Record** pointing `@` and `www` to your frontend host (e.g. Vercel or Render).
   - If using a subdomain for API (e.g. `api.myhobbyboard.com`), add **CNAME** pointing `api` to your backend host URL.

## Author

James Mounts
