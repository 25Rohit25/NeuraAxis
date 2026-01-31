# 🚀 How to Run NEURAXIS Completely

This guide covers all methods to run the complete NEURAXIS platform.

---

## 📋 Architecture Overview

NEURAXIS consists of these components:

| Component                | Technology          | Port      | Description                |
| :----------------------- | :------------------ | :-------- | :------------------------- |
| **Frontend**             | Next.js 15          | 3000      | Web dashboard and UI       |
| **AI Service (Backend)** | FastAPI + Python    | 8000      | AI diagnosis API           |
| **Realtime Service**     | Node.js + Socket.io | 4000      | WebSocket for live updates |
| **Database**             | PostgreSQL 16       | 5432      | Patient and case data      |
| **Cache**                | Redis 7             | 6379      | Session and cache storage  |
| **Storage**              | MinIO (S3)          | 9000/9001 | Medical images storage     |

---

## 🐳 Option 1: Docker (Recommended for Full Stack)

### Prerequisites

- Docker Desktop installed and running
- At least 8GB RAM allocated to Docker

### Steps

```powershell
# 1. Navigate to project root
cd C:\Users\dell\OneDrive\Desktop\NeuraAxis

# 2. Copy environment file (first time only)
copy .env.example .env

# 3. Start all core services
docker-compose up -d --build

# 4. (Optional) Start additional tools (pgAdmin, Redis Commander)
docker-compose --profile tools up -d

# 5. (Optional) Start MinIO storage
docker-compose --profile storage up -d

# 6. View logs
docker-compose logs -f
```

### Access Points (Docker)

| Service         | URL                        | Credentials                  |
| :-------------- | :------------------------- | :--------------------------- |
| Frontend        | http://localhost:3000      | -                            |
| API Docs        | http://localhost:8000/docs | -                            |
| pgAdmin         | http://localhost:5050      | admin@neuraxis.local / admin |
| Redis Commander | http://localhost:8081      | -                            |
| MinIO Console   | http://localhost:9001      | neuraxis / neuraxis123       |

### Stop Docker

```powershell
docker-compose down
```

---

## 💻 Option 2: Local Development (Without Docker)

Run each service separately for development with hot-reload.

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 16 (or use Docker for DB only)
- Redis (or use Docker for cache only)

### Step 1: Start Database & Redis (using Docker)

```powershell
# Start only PostgreSQL and Redis
docker-compose up -d postgres redis
```

### Step 2: Install Dependencies

```powershell
# Root directory - installs all workspaces
cd C:\Users\dell\OneDrive\Desktop\NeuraAxis
cmd /c "npm install --ignore-scripts"
```

### Step 3: Start Frontend + Realtime (Turborepo)

```powershell
# From project root
cmd /c "npm run dev"
```

This starts:

- Frontend at http://localhost:3000 (or 3001 if 3000 is busy)
- Realtime service at ws://localhost:4000

### Step 4: Start AI Service (Python Backend)

Open a **new terminal**:

```powershell
# Navigate to AI service
cd C:\Users\dell\OneDrive\Desktop\NeuraAxis\services\ai-service

# Create virtual environment (first time)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points (Local)

| Service     | URL                             |
| :---------- | :------------------------------ |
| Frontend    | http://localhost:3000           |
| AI API Docs | http://localhost:8000/docs      |
| Dashboard   | http://localhost:3000/dashboard |
| Patients    | http://localhost:3000/patients  |
| Cases       | http://localhost:3000/cases     |
| Analytics   | http://localhost:3000/analytics |

---

## ⚡ Option 3: Quick Start (Frontend Only)

If you just want to explore the UI without backend:

```powershell
cd C:\Users\dell\OneDrive\Desktop\NeuraAxis

# Install dependencies
cmd /c "npm install --ignore-scripts"

# Start development server
cmd /c "npm run dev"
```

> ⚠️ API calls will fail, but you can browse the UI.

---

## 🔧 Troubleshooting

### PowerShell Script Execution Error

If you see "running scripts is disabled on this system":

```powershell
# Option 1: Use cmd instead
cmd /c "npm run dev"

# Option 2: Change execution policy (Admin PowerShell)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use

```powershell
# Find process using port 3000
netstat -ano | findstr :3000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or kill all node processes
taskkill /F /IM node.exe
```

### Docker Build Fails (OneDrive Path Issue)

Move the project outside OneDrive:

```powershell
# Move to C:\Projects
xcopy /E /I "C:\Users\dell\OneDrive\Desktop\NeuraAxis" "C:\Projects\NeuraAxis"
cd C:\Projects\NeuraAxis
docker-compose up -d --build
```

### Database Connection Failed

Wait 30 seconds for PostgreSQL to fully initialize, then restart backend:

```powershell
docker-compose restart backend
```

---

## 📊 Environment Variables

The `.env` file controls configuration. Key variables:

```env
# Database
POSTGRES_DB=neuraxis
POSTGRES_USER=neuraxis_user
POSTGRES_PASSWORD=neuraxis_dev_password

# Redis
REDIS_URL=redis://localhost:6379

# AI/ML (Optional - enables advanced features)
OPENAI_API_KEY=your_key_here
```

---

## 🎯 Quick Reference

| Command                               | Description                           |
| :------------------------------------ | :------------------------------------ |
| `npm run dev`                         | Start frontend + realtime in dev mode |
| `npm run build`                       | Build all packages for production     |
| `npm run docker:up`                   | Start Docker services                 |
| `npm run docker:down`                 | Stop Docker services                  |
| `npm run docker:logs`                 | View Docker logs                      |
| `docker-compose up -d postgres redis` | Start only DB + Cache                 |

---

## ✅ Verification Checklist

After starting, verify these URLs work:

- [ ] http://localhost:3000 - Landing page loads
- [ ] http://localhost:3000/dashboard - Dashboard loads
- [ ] http://localhost:8000/docs - API docs load (if backend running)
- [ ] http://localhost:8000/health - Returns `{"status": "healthy"}`

---

**Happy Coding! 🧠⚡**
