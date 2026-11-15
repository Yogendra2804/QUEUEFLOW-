# QueueFlow — Full-Stack Queue Management System

QueueFlow is a high-performance, local-first queue management platform built for modern service environments—medical clinics, bank counters, administrative desks, and service centers. It provides real-time token tracking, FIFO queue ordering, dynamic waiting time estimation, and a live analytics dashboard.

---

## Key Features

- **Manager Authentication**: Secure registration and login using JWT (HMAC-SHA256) and `bcrypt` password hashing.
- **Multi-Queue Management**: Create, view, edit, and deactivate multiple queues under a single manager account.
- **Deterministic Token Sequencing**: Guaranteed monotonically increasing token numbers per queue using persistent database counters.
- **FIFO Queue Lifecycle**: Real-time position tracking ($1, 2, \dots, N$) maintaining strict First-In-First-Out ordering.
- **Adjacent Swapping Reordering**: Instant one-step prioritized promotion or demotion of waiting customers without global queue re-indexing.
- **Single-Server Guard**: Prevents multiple tokens from being served simultaneously in the same queue.
- **Service & Wait Duration Calculations**: Tracks exact waiting times ($\text{called\_at} - \text{joined\_at}$) and service durations ($\text{completed\_at} - \text{called\_at}$).
- **Historical-Average Wait Estimation**: Dynamically calculates estimated remaining wait times based on actual past service completions.
- **Real-Time Analytics Dashboard**: Visualizes daily token volume, completion rates, cancellation rates, and duration metrics with interactive Recharts diagrams.
- **Responsive & Modern UI**: Built with Tailwind CSS, supporting mobile, tablet, and desktop layouts with feedback states (spinners, toasts, empty states).

---

## Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Frontend** | React 18/19, TypeScript, Vite | Single-page application, strict type safety |
| **Styling** | Tailwind CSS 3 | Utility-first responsive design, component styling |
| **Charts** | Recharts | Declarative SVG bar and line charts |
| **Icons & Toasts** | Lucide React, React Hot Toast | Modern icon set and toast notifications |
| **Backend** | Python 3.12+, FastAPI | Asynchronous ASGI REST API framework |
| **Validation** | Pydantic v2 | Strict schema validation and serialization |
| **Database** | SQLite + SQLAlchemy 2.0 | File-backed ACID transactional persistence |
| **Authentication** | JWT (python-jose) + bcrypt (passlib) | Stateless Bearer token authentication |
| **Testing** | Pytest (Backend), Vitest (Frontend) | Full integration and component test coverage |

---

## Architecture Overview

```
+-----------------------------------------------------------+
|                   Frontend (Port 5173)                    |
|   React + TypeScript + Vite + Tailwind CSS + Recharts    |
|   - Real-time polling & state updates                     |
|   - Axios client with JWT authorization interceptor       |
+-----------------------------+-----------------------------+
                              | REST JSON API
                              v
+-----------------------------------------------------------+
|                    Backend (Port 8000)                    |
|   FastAPI + Pydantic v2 + SQLAlchemy 2.0 ORM              |
|   - Stateless JWT authentication (/api/auth)              |
|   - Queue management controllers (/api/queues)            |
|   - Token lifecycle & ordering engine (/api/tokens)       |
|   - Aggregated analytical engine (/api/analytics)         |
+-----------------------------+-----------------------------+
                              | SQLAlchemy Session
                              v
+-----------------------------------------------------------+
|                 Persistent SQLite Database                |
|   queueflow.db (ACID relational storage)                  |
|   - Tables: managers, queues, tokens                      |
+-----------------------------------------------------------+
```

---

## Local Development Setup

### Prerequisites

- **Python**: 3.11 or 3.12+ installed
- **Node.js**: v20+ with `npm` installed
- **Operating System**: Windows (PowerShell scripts included) or macOS/Linux

---

### Step 1: Clone the Repository

```powershell
git clone https://github.com/Yogendra2804/QUEUEFLOW-.git
cd QUEUEFLOW-
```

---

### Step 2: Backend Setup

1. Open PowerShell and navigate to the `backend` folder:
   ```powershell
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install required Python packages:
   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```powershell
   Copy-Item .env.example .env
   ```
   *(The default `.env` is pre-configured for local development with SQLite).*

5. Run database migrations / initialization (tables auto-initialize on startup):
   ```powershell
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Backend will be available at: **`http://localhost:8000`**  
   Interactive OpenAPI documentation: **`http://localhost:8000/docs`**

---

### Step 3: Frontend Setup

1. Open a new PowerShell terminal and navigate to the `frontend` folder:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Configure environment variables (pre-configured to target backend port 8000):
   ```powershell
   Copy-Item .env.example .env
   ```

4. Start the Vite development server:
   ```powershell
   npm run dev
   ```
   Frontend will be available at: **`http://localhost:5173`**

---

## Convenient Startup Scripts (Windows)

Convenient one-click PowerShell startup scripts are provided in the project root:

- **Start Backend**:
  ```powershell
  .\start-backend.ps1
  ```
- **Start Frontend**:
  ```powershell
  .\start-frontend.ps1
  ```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default Value | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-...` | Secret key for JWT signature hashing |
| `ALGORITHM` | `HS256` | JWT signature algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token expiration time in minutes |
| `DATABASE_URL` | `sqlite:///./queueflow.db` | SQLite connection string |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origin for CORS |

### Frontend (`frontend/.env`)

| Variable | Default Value | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

---

## REST API Reference

Interactive API documentation with Swagger UI is accessible at `http://localhost:8000/docs`.

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Register a new manager account.
- `POST /api/auth/login` — Authenticate and receive a Bearer JWT token.
- `GET /api/auth/me` — Retrieve the profile of the authenticated manager.

### Queues (`/api/queues`)
- `GET /api/queues/` — List all active queues owned by the manager.
- `POST /api/queues/` — Create a new queue.
- `GET /api/queues/{queue_id}` — Get queue details including live waiting and serving counts.
- `PUT /api/queues/{queue_id}` — Update queue name or description.
- `DELETE /api/queues/{queue_id}` — Soft-delete a queue.

### Tokens & Operations (`/api/queues/{queue_id}/tokens`)
- `GET /` — List all active (`waiting` and `serving`) tokens in order.
- `POST /` — Register a person and issue a sequential token.
- `POST /call-next` — Transition the front waiting token to `serving` (FIFO).
- `POST /{token_id}/complete` — Mark token as completed and log timestamps.
- `POST /{token_id}/cancel` — Cancel a token and re-index following positions.
- `POST /{token_id}/move-up` — Swap waiting token position with previous token.
- `POST /{token_id}/move-down` — Swap waiting token position with next token.

### Analytics (`/api/analytics`)
- `GET /api/analytics/` — Compute aggregated stats, wait averages, and 7-day breakdowns across queues.

---

## Automated Testing

### Backend Tests (Pytest)

Run all 29 automated backend tests against an in-memory SQLite database:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -v
```

**Test Coverage Summary**:
- Manager registration, unique email constraint, password hashing.
- Login validation, invalid credentials, token expiration handling.
- Cross-manager tenant isolation (IDOR verification).
- Sequential token numbering and FIFO order retention.
- Adjacent swap reordering (`move-up`, `move-down`) and edge conditions.
- Single-serving token enforcement (blocking second calls).
- State transitions (waiting -> serving -> completed / cancelled).
- Automatic position compaction upon token removal.
- Real SQL analytics aggregation.

### Frontend Build & Typecheck

```powershell
cd frontend
npm run build
```

---

## Screenshots & Workflow

### 1. Manager Authentication
Clean, secure sign-in and registration pages equipped with validation and instant feedback.

### 2. Multi-Queue Dashboard
Overview of all active queues displaying live customer counts, quick management links, and inline queue renaming.

### 3. Active Queue Management
Real-time view with:
- Prominent **"Now Serving"** banner with service timers.
- Sequential waiting list with token numbers, names, phone numbers, and estimated wait times.
- Step-wise adjacent reordering controls (Arrow Up / Down).
- Single-click **"Call Next"** and **"Complete"** workflow.

### 4. Real-Time Analytics Dashboard
- Summary stat cards: Total Queues, Tokens Today, Completed Today, Cancelled Today.
- Average Wait Time and Average Service Duration.
- Per-queue breakdown cards with 7-day volume bar charts.
- Aggregate 7-day performance line chart.
