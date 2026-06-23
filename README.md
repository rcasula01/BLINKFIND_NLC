

# BlinkFind STEM

**A secure, student-friendly lost & found platform — reunite students with their belongings in the blink of an eye.**


---

##  Table of Contents

- [About](#-about)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Authentication Flow](#-authentication-flow)
- [Usage](#-usage)
- [Authors](#-authors)

---

##  About

**BlinkFind STEM** is a full-stack lost and found web application built specifically for schools and STEM programs. Students can report found items, browse unclaimed belongings, and submit claims — all through a clean, intuitive interface. Admins get a dedicated dashboard to review, approve, or reject claims with full control.

No more paper sign-up sheets. No more cluttered lost-and-found bins nobody checks.

---

## Features

| Feature | Description |
|---|---|
| **Report Items** | Submit found items with photos, descriptions, and location details |
|  **Search & Filter** | Browse and filter lost items to find what you're looking for |
|  **Claim Items** | Submit a claim for an item — securely and easily |
| **Admin Dashboard** | Approve, reject, or delete item reports and claims |
| **Image Preview** | Live image preview when uploading found items |
| **Secure Auth** | Server-side Supabase authentication with signed session cookies |

---

## 📁 Project Structure

```
/project-root
│
├── index.html          → Admin login page
├── home.html           → Admin home (requires login)
├── report.html         → Form to report found items
├── claim.html          → Browse and claim items
├── admin.html          → Admin dashboard (requires login)
│
├── styles.css          → Global site styling
│
├── report.js           → Item submission + image preview logic
├── claim.js            → Search, filter, and claim items
├── admin.js            → Dashboard logic (approve / reject / delete)
├── login.js            → Frontend login — calls /auth/login on the Flask backend
├── supabase.js         → API layer (communicates with Flask backend)
│
├── server.py           → Flask backend server (API + auth endpoints)
├── requirements.txt    → Python dependencies
│
├── .env.example        → Environment variable template (copy to .env)
└── .gitignore          → Excludes secrets and build artefacts
```

---

##  Tech Stack

### Frontend
- **HTML5** — structure and markup
- **CSS3** — design, layout, and responsiveness
- **Vanilla JavaScript (ES6)** — interactivity and client-side logic

### Backend
- **Python / Flask** — REST API server + auth endpoints
- **SQLite** — lightweight local database
- **Flask-CORS** — cross-origin request support
- **supabase-py** — Supabase Python client for server-side auth
- **python-dotenv** — loads environment variables from `.env`

---

## Getting Started

### Prerequisites

- Python 3.9+
- A [Supabase](https://supabase.com) account and project (free tier is fine)
- A virtual environment (recommended)

### 1. Create a Supabase Project

1. Sign in at [supabase.com](https://supabase.com) and click **New project**.
2. Once created, go to **Project Settings → API** and copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY` *(keep this secret)*
3. Go to **Authentication → Users** and create at least one user (email + password).

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SESSION_SECRET=a-long-random-secret-string
```

> **Important:** Never commit your `.env` file. It is already listed in `.gitignore`.

### 3. Set Up the Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# OR
venv\Scripts\activate           # Windows
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the Flask Backend

Open **Terminal 1** and run:

```bash
source venv/bin/activate
python server.py
```

You should see:

```
🚀 Starting BlinkFind Server...
Running on http://127.0.0.1:4000
```

### 6. Start the Frontend Server

Open **Terminal 2** and run:

```bash
python -m http.server 8000
```

### 7. Open in Your Browser

```
http://localhost:8000
```

---

##  Authentication Flow

BlinkFind uses **server-side Supabase authentication** backed by signed Flask session cookies.

```
Browser                     Flask (port 4000)              Supabase Auth
  │                               │                              │
  │  POST /auth/login             │                              │
  │  { email, password }  ──────► │                              │
  │                               │  sign_in_with_password ────► │
  │                               │ ◄──── session + user ────────│
  │ ◄── Set-Cookie: session ──────│                              │
  │                               │                              │
  │  GET /auth/session    ──────► │                              │
  │  (Cookie sent auto)           │  get_user(token) ──────────► │
  │ ◄── { authenticated: true } ──│ ◄──── user info ─────────────│
  │                               │                              │
  │  POST /auth/logout    ──────► │                              │
  │ ◄── { success: true } ────────│  sign_out()  ──────────────► │
  │  (Cookie cleared)             │                              │
```

- **Credentials never reach the browser** — no tokens, keys, or passwords are stored in localStorage or JS variables.
- Session is maintained via an **HttpOnly cookie** signed with `SESSION_SECRET`.
- `admin.html` and `home.html` enforce an auth guard: unauthenticated users are immediately redirected to `index.html`.

---

##  Usage

| Page | URL | Description |
|---|---|---|
| Login | `/index.html` | Admin login page |
| Home | `/home.html` | Admin home (requires login) |
| Report | `/report.html` | Submit a found item |
| Claim | `/claim.html` | Browse and claim items |
| Admin Dashboard | `/admin.html` | Manage all reports and claims (requires login) |

---


##  Authors

**Rutviij Casula**
 [Rutviij.Casula21@gmail.com](mailto:Rutviij.Casula21@gmail.com)

Made with ❤️ for Downingtown STEM Students.

