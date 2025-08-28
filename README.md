# Collaborative Drawing Board

A real-time collaborative drawing application built with strict Test-Driven Development (TDD).

## Tech Stack

- **Frontend**: React + TypeScript + Konva.js
- **Backend**: FastAPI + Python + GraphQL
- **Database**: PostgreSQL
- **Cache/PubSub**: Redis
- **Security**: End-to-end encryption (AES-GCM)
- **Real-time**: WebSocket synchronization

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start
```bash
# Start all services
docker-compose up --build

# Access the application
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

### Local Development

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

### Testing

#### Backend Tests
```bash
cd backend
pytest
```

#### Frontend Tests
```bash
cd frontend
npm test
```

## TDD Workflow

This project follows strict Test-Driven Development:
1. Write failing tests first
2. Write minimal code to pass tests
3. Refactor while keeping tests green
4. Repeat

## Project Status

✅ Phase 1: Project skeleton setup complete
🔄 Phase 2: Ready for TDD development