# ヨシコさん、ヨシッ！(Yoshiko-san, Yoshi!)

現場の「よし！」を、最強の安全装置に変える

A next-generation industrial safety management system that digitizes Japan's "指差呼称" (pointing and calling) safety practice using multimodal AI.

## 🏗️ Architecture

```
Client (yoshikosan.ameyanagi.com:6666)
    ↓
┌─────────────────────────────────────┐
│  Nginx Reverse Proxy (Port 6666)   │
└─────────────────────────────────────┘
    ↓                    ↓
    /                    /api/*
    ↓                    ↓
┌──────────────┐    ┌──────────────┐
│  Frontend    │    │   Backend    │
│  Next.js 16  │    │  FastAPI     │
│  (Port 3000) │    │  (Port 8000) │
└──────────────┘    └──────────────┘
                         ↓
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │  Database    │
                    └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Bun (for frontend development)
- Poetry or uv (for backend development)

### Setup

1. **Clone and configure environment**
   ```bash
   cd /home/ryuichi/dev/yoshikosan
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

2. **Build and run with Docker**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://yoshikosan.ameyanagi.com:6666/
   - Backend API: http://yoshikosan.ameyanagi.com:6666/api/
   - API Docs: http://yoshikosan.ameyanagi.com:6666/docs

## 📁 Project Structure

```
/
├── yoshikosan-frontend/     # Next.js 16 frontend
│   ├── app/                # App Router pages
│   ├── components/         # React components
│   ├── lib/               # Utilities
│   └── Dockerfile
├── yoshikosan-backend/      # FastAPI backend
│   ├── src/               # Source code
│   │   ├── domain/       # DDD: Domain layer
│   │   ├── application/  # DDD: Application layer
│   │   ├── infrastructure/ # DDD: Infrastructure layer
│   │   └── api/          # API endpoints
│   ├── tests/            # Backend tests
│   └── Dockerfile
├── openspec/              # OpenSpec proposals
├── docker-compose.yml     # Multi-service orchestration
├── nginx.conf            # Nginx configuration
├── .env                  # Environment variables (gitignored)
└── README.md
```

## 🛠️ Development

### Backend Development
```bash
cd yoshikosan-backend
poetry install
poetry run uvicorn src.main:app --reload --port 8000
```

### Frontend Development
```bash
cd yoshikosan-frontend
bun install
bun dev
```

### Run Tests
```bash
# Backend unit tests only (no frontend tests for MVP)
cd yoshikosan-backend
poetry run pytest
```

## 🔧 Key Technologies

**Frontend:**
- Next.js 16 (App Router)
- React 19
- TypeScript 5
- Tailwind CSS v4
- Bun

**Backend:**
- FastAPI
- Python 3.12+
- SQLAlchemy 2.0 (async)
- PostgreSQL
- Pydantic v2

**AI/ML:**
- SambaNova (LLM for SOP structuring & verification)
- Hume AI (Empathic TTS)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)

## 🎯 MVP Features

- [ ] SOP upload and structuring (image → JSON via SambaNova)
- [ ] Manual "Yoshi!" verification button
- [ ] Single-image capture and AI verification
- [ ] TTS feedback with OK/NG guidance (Hume AI)
- [ ] Basic safety check logging
- [ ] User authentication (JWT + OAuth)

## 📚 Documentation

For detailed documentation, see:
- [Project Context](openspec/project.md) - Comprehensive project documentation
- [OpenSpec Agents](openspec/AGENTS.md) - Agent instructions for AI assistants

## 🔒 Security Notes

- All secrets should be stored in `.env` (never commit this file)
- Use strong passwords for `SECRET_KEY` and `POSTGRES_PASSWORD`
- Update `ALLOWED_ORIGINS` to match your actual domain
- In production, remove `/docs` endpoint from Nginx config

## 📝 License

[Add your license here]

## 👥 Contributors

[Add contributors here]
# Yoshikosan
