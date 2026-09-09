# MyHobbyBoard

MyHobbyBoard is a full-stack web application built for hobbyists, makers, and builders to track project ideas, manage tasks, and document milestone progress with media and community updates.

**Live site:** [https://myhobbyboard.com](https://myhobbyboard.com)

## Features

- **Authentication & Security:** JWT authentication with password hashing (minimum 8-character passwords), secure token storage, ownership-based authorization, and rate limiting on auth and AI endpoints.
- **Project & Task Management:** Full CRUD project workspaces with material checklists, notes, status tracking, and priority tagging.
- **Progress Tracking & Visuals:** Live dashboard analytics, milestone updates with photo and video uploads.
- **AI Planning Assistant:** Intelligent project milestone and prep recommendations powered by Google Gemini (with resilient built-in fallbacks), gated behind login and rate-limited to prevent abuse.
- **Social Discovery & Follows:** Public project discovery, granular board-level follows, milestone feeds, and update comments.
- **Production Architecture:** Decoupled React frontend and Flask backend, persistent Postgres database, and cloud media storage so user data survives every deploy.

## Tech Stack

Frontend:
- React 19
- React Router 7
- Vite 8
- CSS3 (custom design system)
- Hosted on Render (Static Site)

Backend:
- Python 3.12+
- Flask & Gunicorn
- Flask-SQLAlchemy + Neon (serverless Postgres, production) / SQLite (local dev)
- Flask-Migrate & Alembic
- Flask-JWT-Extended
- Flask-Limiter (rate limiting on signup, login, and the AI assistant)
- Flask-CORS
- Hosted on Render (Web Service)

Third-party services:
- **Google Gemini** (`gemini-3.6-flash`) for the Planning Assistant, with local fallback suggestions if no key is configured or the request fails
- **Cloudinary** for persistent photo/video storage on board updates (falls back to local disk when unset, e.g. local development)
- **Neon** for the production Postgres database

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
- `GET /api/uploads/:filename` (protected token download, local-dev fallback only; production media is served directly from Cloudinary URLs)

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

### 1. Clone the Repository

```bash
git clone https://github.com/mounts10-wq/My-Hobby-Board.git
cd My-Hobby-Board
```

### 2. Backend Setup

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

### 3. Frontend Setup

Open a second terminal:

```bash
cd client
npm install
cp .env.example .env
npm run dev
```

Runs at: `http://127.0.0.1:5173`

### 4. Running Verification Tests

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

## Production Deployment

The live site runs on this stack:

| Layer | Service |
| :--- | :--- |
| Frontend hosting | Render (Static Site) |
| Backend hosting | Render (Web Service, Gunicorn) |
| Database | Neon (serverless Postgres, free tier) |
| Media storage | Cloudinary (free tier) |
| AI Assistant | Google Gemini (`gemini-3.6-flash`, free tier) |
| Domain / DNS | Network Solutions |

### Backend Deployment (Render Web Service)
1. Push the repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), create a **New Web Service**:
   - **Root Directory:** `server`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app`
3. Add Environment Variables:
   - `SECRET_KEY`: random 32+ char string
   - `JWT_SECRET_KEY`: random 32+ char string
   - `DATABASE_URL`: your Neon **pooled connection** string (`postgresql://...?sslmode=require`)
   - `GEMINI_API_KEY`: free key from [Google AI Studio](https://aistudio.google.com/)
   - `GEMINI_MODEL`: `gemini-3.6-flash`
   - `CLOUDINARY_URL`: from your Cloudinary dashboard (`cloudinary://<api_key>:<api_secret>@<cloud_name>`)
   - `CORS_ORIGINS`: `https://myhobbyboard.com,https://www.myhobbyboard.com`

### Database (Neon)
1. Create a free project at [neon.tech](https://neon.tech).
2. Copy the **pooled connection string** from the project dashboard.
3. Paste it into the backend's `DATABASE_URL` environment variable on Render.
4. Tables are created automatically on app startup — no manual migration needed for a fresh database.

### Media Storage (Cloudinary)
1. Create a free account at [cloudinary.com](https://cloudinary.com).
2. Copy the **API Environment variable** shown on your dashboard (`CLOUDINARY_URL=cloudinary://...`).
3. Paste the value into the backend's `CLOUDINARY_URL` environment variable on Render.
4. Without this set, uploaded media falls back to local disk, which is fine for local development but is **not persistent** on most hosting platforms.

### Frontend Deployment (Render Static Site)
1. In Render, create a **New Static Site**:
   - **Root Directory:** `client`
   - **Build Command:** `npm run build`
   - **Publish Directory:** `dist`
2. Add Environment Variable:
   - `VITE_API_BASE_URL`: your backend's Render URL with `/api` appended (e.g. `https://my-hobby-board.onrender.com/api`)
3. Add a rewrite rule so client-side routing works on refresh/direct links:
   - **Source:** `/*` → **Destination:** `/index.html` → **Action:** `Rewrite`

### Custom Domain Setup
1. In your Render Static Site → **Settings** → **Custom Domains**, add `myhobbyboard.com` and `www.myhobbyboard.com`.
2. In your domain registrar's DNS settings, add the exact A/ALIAS and CNAME records Render provides.
3. Render automatically issues a free SSL certificate once DNS is verified.

## Troubleshooting

- If the frontend shows "The server is unavailable," confirm `VITE_API_BASE_URL` on the frontend matches the backend's actual Render URL, and that the backend service is deployed and awake (Render's free tier spins down after 15 minutes idle; the first request afterward can take 30-50 seconds).
- If the Planning Assistant always returns `"source": "fallback"`, check the backend logs on Render for `Gemini assistant call failed`. Common causes are an invalid/expired `GEMINI_API_KEY` or a retired `GEMINI_MODEL` name — confirm available models for your key at `https://generativelanguage.googleapis.com/v1beta/models?key=<your-key>`.
- If signups/boards seem to reset after a deploy, `DATABASE_URL` is likely still pointing at local SQLite instead of Neon.
- If uploaded photos/videos disappear after a deploy, `CLOUDINARY_URL` is not set on the backend, so uploads are falling back to local disk.

## Author

James Mounts
