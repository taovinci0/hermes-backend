# Hermes Frontend Development Guide

**Date**: November 13, 2025  
**Purpose**: Guide for building frontend dashboard in Hermes monorepo  
**Structure**: Monorepo - All components in one repository

---

## 🎯 Overview

Hermes uses a **monorepo structure** - everything (trading engine, API backend, frontend) lives in one Git repository under separate folders.

**Key Principle**: One repo, separate folders, all versioned together.

---

## 📁 Monorepo Structure

```
hermes-v1.0.0/                          # ONE Git repository
├── README.md                           # Project overview
├── .gitignore
├── .env.sample
├── pyproject.toml                      # Python dependencies
│
├── core/                               # Trading engine (Python)
│   ├── config.py
│   ├── orchestrator.py
│   ├── registry.py
│   └── ...
│
├── agents/                             # Trading agents (Python)
│   ├── zeus_forecast.py
│   ├── prob_mapper.py
│   ├── backtester.py
│   ├── dynamic_trader/
│   └── ...
│
├── venues/                             # Market integrations (Python)
│   └── polymarket/
│
├── data/                               # Data storage
│   ├── registry/
│   ├── snapshots/
│   ├── trades/
│   └── runs/
│
├── tests/                              # Python tests
│
├── backend/                            # NEW - FastAPI backend
│   ├── api/
│   │   ├── main.py                     # FastAPI app entry
│   │   ├── routes/                     # API endpoints
│   │   ├── services/                   # Business logic
│   │   ├── models/                     # Pydantic schemas
│   │   └── utils/                      # Helpers
│   ├── tests/
│   ├── requirements.txt                # fastapi, uvicorn, etc.
│   └── README.md
│
├── frontend/                           # NEW - Frontend dashboard
│   ├── src/                            # (React) or dashboard.py (Streamlit)
│   ├── package.json                    # (React) or requirements.txt (Streamlit)
│   └── README.md
│
├── docs/                               # Documentation
│   └── build/
│       ├── FRONTEND.md                 # UI/UX design
│       ├── STAGE_7D_SPECIFICATION.md   # API backend spec
│       └── FRONT_END_DEV.md            # This file
│
└── docker-compose.yml                  # (Optional) Run everything together
```

---

## 🎯 Why Monorepo?

### Benefits:

✅ **Single source of truth** - Everything versioned together  
✅ **Easier development** - One `git clone`, one repository  
✅ **Atomic updates** - Update trading engine + API + frontend in one commit  
✅ **Shared code** - Backend can import Hermes directly (`from core import config`)  
✅ **Simpler deployment** - One repo to deploy  
✅ **Better for small teams** - No coordination overhead

### Structure:

- **Folders** = Organization (`backend/`, `frontend/`, `core/`)
- **One repo** = Single Git repository
- **All together** = Versioned, deployed, and developed together

---

## 🚀 Local Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/taovinci0/hermes-backend.git
cd hermes-backend
```

### Step 2: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install trading engine dependencies
pip install -e ".[dev]"

# Install backend API dependencies (if building API)
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: Setup Frontend

**Option A: Streamlit (Recommended for MVP)**
```bash
pip install streamlit pandas plotly
mkdir frontend
# Create frontend/dashboard.py
```

**Option B: React (Production quality)**
```bash
cd frontend
npm install
cd ..
```

### Step 4: Configure Environment

```bash
# Copy sample env
cp .env.sample .env

# Edit with your API keys
nano .env  # or use your editor
```

### Step 5: Start Development

**Option 1: Manual (3 terminals)**

```bash
# Terminal 1: Trading engine
python -m core.orchestrator --mode dynamic-paper --stations EGLC,KLGA

# Terminal 2: Backend API (if using React frontend)
cd backend
uvicorn api.main:app --reload --port 8000

# Terminal 3: Frontend
# Streamlit:
streamlit run frontend/dashboard.py

# OR React:
cd frontend
npm run dev
```

**Option 2: Docker Compose (Production-like)**

```bash
docker-compose up
```

**Access Points:**
- **Streamlit**: http://localhost:8501
- **React**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📦 Creating the Folders

### Create Backend Structure

```bash
cd /Users/harveyando/Local\ Sites/hermes-v1.0.0

# Create backend directory structure
mkdir -p backend/api/{routes,services,models,utils}
mkdir -p backend/tests

# Create __init__.py files
touch backend/__init__.py
touch backend/api/__init__.py
touch backend/api/routes/__init__.py
touch backend/api/services/__init__.py
touch backend/api/models/__init__.py
touch backend/api/utils/__init__.py

# Create main files
touch backend/api/main.py
touch backend/requirements.txt
touch backend/README.md

echo "✅ Backend structure created!"
```

### Create Frontend Structure

**Streamlit Option:**
```bash
mkdir -p frontend
touch frontend/dashboard.py
touch frontend/requirements.txt

# Add to requirements.txt:
# streamlit
# pandas
# plotly

echo "✅ Frontend (Streamlit) structure created!"
```

**React Option:**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @tanstack/react-query recharts tailwindcss axios
cd ..

echo "✅ Frontend (React) structure created!"
```

---

## 🎨 Frontend Options

### Option 1: Streamlit (Recommended for MVP)

**Timeline**: 1 week  
**Complexity**: Low  
**Tech**: All Python

**Pros:**
- ✅ Fast to build (3-5 days)
- ✅ No API needed (reads files directly!)
- ✅ All Python (no JavaScript)
- ✅ Good for internal tools
- ✅ Can upgrade to React later

**Cons:**
- ⚠️ Less customizable
- ⚠️ Limited real-time updates
- ⚠️ Python-only stack

**When to use:**
- Want dashboard THIS WEEK
- Internal tool (not public-facing)
- Small team (1-3 developers)

**Setup:**
```bash
pip install streamlit pandas plotly
mkdir frontend
# Create frontend/dashboard.py
streamlit run frontend/dashboard.py
```

---

### Option 2: React (Production Quality)

**Timeline**: 3-4 weeks  
**Complexity**: Medium-High  
**Tech**: TypeScript, React, Vite

**Pros:**
- ✅ Professional UI
- ✅ Better performance
- ✅ More customizable
- ✅ Real-time WebSocket support
- ✅ Modern user experience

**Cons:**
- ⚠️ Longer development time
- ⚠️ Requires FastAPI backend
- ⚠️ JavaScript/TypeScript needed

**When to use:**
- Production-facing application
- Need advanced features
- Want best user experience
- Have time for full build

**Setup:**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @tanstack/react-query recharts tailwindcss axios
npm run dev
```

**Requires**: FastAPI backend (Stage 7D)

---

## 🔧 Development Workflows

### Workflow 1: Streamlit (No API Needed)

**Simplest approach** - Streamlit reads files directly:

```bash
# Terminal 1: Trading engine
python -m core.orchestrator --mode dynamic-paper --stations EGLC,KLGA &

# Terminal 2: Streamlit dashboard
streamlit run frontend/dashboard.py
```

**Access**: http://localhost:8501

**Benefits:**
- ✅ No API to build
- ✅ Fastest to get working
- ✅ All Python

---

### Workflow 2: React + FastAPI

**Full-stack approach** - React frontend + FastAPI backend:

```bash
# Terminal 1: Trading engine
python -m core.orchestrator --mode dynamic-paper --stations EGLC,KLGA &

# Terminal 2: Backend API
cd backend
uvicorn api.main:app --reload --port 8000 &

# Terminal 3: React frontend
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Benefits:**
- ✅ Professional UI
- ✅ Real-time updates
- ✅ Scalable architecture

---

### Workflow 3: Docker Compose

**Production-like environment** - Everything in containers:

```bash
# Start everything
docker-compose up

# Or in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

**Benefits:**
- ✅ Consistent environment
- ✅ Matches production
- ✅ One command to start

---

## 🐳 Docker Setup (Optional)

### docker-compose.yml

```yaml
version: '3.8'

services:
  # Trading engine (dynamic paper mode)
  trading-engine:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: hermes-trading
    command: python -m core.orchestrator --mode dynamic-paper --stations EGLC,KLGA
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - hermes-network

  # Backend API
  api:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: hermes-api
    command: uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - trading-engine
    restart: unless-stopped
    networks:
      - hermes-network

  # Frontend (development)
  frontend-dev:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: hermes-frontend-dev
    command: npm run dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - api
    networks:
      - hermes-network

networks:
  hermes-network:
    driver: bridge
```

---

## 🚀 Production Deployment

### Option 1: Single VPS (Simplest)

**Hosting**: DigitalOcean, AWS EC2, Linode

**Setup:**
```bash
# On server
git clone https://github.com/taovinci0/hermes-backend.git
cd hermes-backend

# Setup environment
cp .env.sample .env
nano .env  # Add API keys

# Run with Docker
docker-compose -f docker-compose.prod.yml up -d
```

**Cost**: $10-20/month

---

### Option 2: Separate Services (Scalable)

**Hosting**: Railway, Render, Fly.io

**Trading Engine**: Railway (background worker)  
**API**: Railway (web service)  
**Frontend**: Vercel/Netlify (static hosting)

**Cost**: $15-30/month

---

## 📋 Recommended Path for Hermes

### Phase 1: Streamlit MVP (This Week)

**Goal**: Get dashboard working quickly

1. Create `frontend/dashboard.py`
2. Build Streamlit dashboard (3-5 days)
3. Test with live trading data
4. Deploy locally

**Result**: Working dashboard in 1 week

---

### Phase 2: Evaluate Need for React (Next Week)

**After using Streamlit**, decide:

**Option A**: Streamlit is good enough
- ✅ Keep it
- ✅ You're done!

**Option B**: Need more features
- Build FastAPI backend (2 weeks)
- Build React frontend (3 weeks)

---

### Phase 3: Add Docker (When Deploying)

**When ready for production**:

1. Create `docker-compose.yml`
2. Create `Dockerfile.backend` and `Dockerfile.frontend`
3. Test locally with Docker
4. Deploy to VPS

---

## 🎯 Quick Start Commands

### Create Backend Structure

```bash
cd /Users/harveyando/Local\ Sites/hermes-v1.0.0
mkdir -p backend/api/{routes,services,models,utils}
mkdir -p backend/tests
touch backend/api/main.py backend/requirements.txt
```

### Create Streamlit Frontend

```bash
mkdir frontend
pip install streamlit pandas plotly
touch frontend/dashboard.py
```

### Create React Frontend

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install && cd ..
```

---

## 📚 Related Documentation

- **FRONTEND.md**: Complete UI/UX design and specifications
- **STAGE_7D_SPECIFICATION.md**: FastAPI backend API specification
- **README.md**: Overall project overview

---

## ✅ Summary

**Structure**: Monorepo - One repo, separate folders  
**Backend**: `backend/` folder (FastAPI)  
**Frontend**: `frontend/` folder (Streamlit or React)  
**Development**: Local first, Docker for production  
**Deployment**: VPS with Docker Compose

**Start Simple**: Streamlit dashboard (1 week)  
**Upgrade Later**: React + FastAPI (if needed)

---

**Ready to build!** 🚀

**Author**: Hermes Development Team  
**Date**: November 13, 2025

