# 🎨 Collaborative Drawing Board

> **A production-ready, real-time collaborative drawing application with end-to-end encryption, built using strict Test-Driven Development (TDD)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-v18+-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-v5+-3178c6.svg)](https://www.typescriptlang.org/)

## 🌟 Overview

The Collaborative Drawing Board enables multiple users to draw together in real-time with **military-grade end-to-end encryption**. Built with a **web-first architecture** and **TDD methodology**, this application demonstrates modern full-stack development practices suitable for both portfolio showcases and production deployment.

### ✨ Core Features

- 🎨 **Real-time Collaborative Drawing**: Multiple users can draw simultaneously using HTML5 Canvas (Konva.js)
- 🔐 **End-to-End Encryption**: All strokes encrypted client-side using AES-GCM before transmission
- 🖊️ **Advanced Drawing Tools**: Pen size selector, color picker, undo/redo, clear functions
- 👀 **Live Cursor Awareness**: See other participants' cursors in real-time
- 💾 **Persistent Boards**: Save and restore drawing sessions from PostgreSQL
- 📱 **Gallery & Exports**: Export drawings as PNG images or WebM animations
- ⚡ **Low Latency Sync**: Optimized for minimal drawing lag using WebSockets + Yjs CRDT
- 🔒 **Secure Authentication**: JWT-based auth with bcrypt password hashing

### 🏗️ Architecture Highlights

- **Conflict-Free Collaborative Editing**: Yjs CRDT ensures consistent state across all clients
- **Security-First Design**: Zero-trust architecture with client-side encryption
- **Performance Optimized**: RequestAnimationFrame rendering, Redis caching, connection pooling
- **Container-Ready**: Full Docker Compose development and deployment environment
- **Future-Mobile Ready**: Clean API separation enables Flutter mobile app expansion

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React + TypeScript + Konva.js | Canvas rendering, UI controls, type safety |
| **Backend** | FastAPI + Strawberry GraphQL | RESTful + GraphQL APIs, WebSocket handling |
| **Real-time** | WebSockets + Yjs CRDT | Conflict-free collaborative synchronization |
| **Database** | PostgreSQL | Persistent storage for users, boards, encrypted strokes |
| **Cache/PubSub** | Redis | Session management, real-time message brokering |
| **Storage** | Local Filesystem / Supabase | Image and animation export storage |
| **Encryption** | AES-GCM (Web Crypto API) | Client-side end-to-end encryption |
| **Containerization** | Docker + Docker Compose | Development and deployment environments |
| **Testing** | pytest + Jest + RTL + Cypress | Comprehensive TDD test coverage |
| **Export** | FFmpeg | PNG image and WebM animation generation |

## 📊 Database Schema

```sql
-- Users table: Authentication and user management
Users (
  id SERIAL PRIMARY KEY,
  username VARCHAR UNIQUE NOT NULL,
  email VARCHAR UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Boards table: Drawing board metadata and encryption keys
Boards (
  id SERIAL PRIMARY KEY,
  name VARCHAR NOT NULL,
  owner_id INT REFERENCES Users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  encrypted_key TEXT NOT NULL,  -- AES-GCM key for board encryption
  is_public BOOLEAN DEFAULT FALSE
);

-- Strokes table: Encrypted drawing stroke data
Strokes (
  id SERIAL PRIMARY KEY,
  board_id INT REFERENCES Boards(id) ON DELETE CASCADE,
  user_id INT REFERENCES Users(id),
  encrypted_data BYTEA NOT NULL,      -- Encrypted stroke coordinates
  iv BYTEA NOT NULL,                  -- AES-GCM initialization vector
  color VARCHAR DEFAULT '#000000',
  size INT DEFAULT 5,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX(board_id, created_at)         -- Optimized for timeline queries
);

-- Gallery table: Exported board images and animations
Gallery (
  id SERIAL PRIMARY KEY,
  board_id INT REFERENCES Boards(id) ON DELETE CASCADE,
  export_type VARCHAR CHECK (export_type IN ('png', 'webm')),
  file_url TEXT NOT NULL,
  file_size BIGINT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔒 Security Architecture

### End-to-End Encryption Flow

1. **Key Generation**: Each board generates a unique AES-GCM 256-bit key client-side
2. **Stroke Encryption**: Drawing coordinates encrypted before WebSocket transmission
3. **Server Blind Storage**: Backend stores only ciphertext, never plaintext stroke data
4. **Client Decryption**: Authorized users decrypt strokes locally for rendering

```typescript
// Client-side encryption example
const encryptStroke = async (strokeData: StrokeData, boardKey: CryptoKey) => {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    boardKey,
    new TextEncoder().encode(JSON.stringify(strokeData))
  );
  return { encrypted: new Uint8Array(encrypted), iv };
};
```

### Security Features

- 🔐 **Zero-Trust Architecture**: Server never accesses plaintext drawing data
- 🛡️ **SQL Injection Prevention**: Parameterized queries with SQLAlchemy ORM
- 🔑 **Secure Authentication**: JWT tokens with rotation, bcrypt password hashing
- 🚫 **Input Validation**: Comprehensive Pydantic schemas and TypeScript interfaces
- 🌐 **CORS Protection**: Configured for production security
- 📝 **Audit Logging**: All actions logged for security monitoring

## ⚡ Performance Optimization

### Low-Latency Drawing Experience

- **RequestAnimationFrame Rendering**: Smooth 60fps drawing updates
- **Batched WebSocket Messages**: Multiple strokes sent in single frames
- **Redis Connection Pooling**: Optimized for concurrent user sessions
- **Efficient Canvas Updates**: Only redraw dirty regions using Konva.js
- **CRDT Conflict Resolution**: Yjs ensures consistent state without locking

### Scalability Considerations

- **Horizontal Backend Scaling**: Stateless FastAPI with Redis session storage
- **Database Connection Pooling**: PostgreSQL optimization for high concurrent loads
- **WebSocket Load Balancing**: Redis pub/sub enables multi-server deployments
- **CDN-Ready Exports**: Static file generation for efficient content delivery

## 🧪 Test-Driven Development (TDD)

### TDD Workflow

```mermaid
graph LR
    A[Write Failing Test] --> B[Write Minimal Code]
    B --> C[Run Tests]
    C --> D{All Tests Pass?}
    D -->|No| B
    D -->|Yes| E[Refactor]
    E --> F[Run Tests Again]
    F --> G{Still Passing?}
    G -->|No| E
    G -->|Yes| A
```

### Testing Strategy & Coverage Targets

| Layer | Framework | Coverage Target | Focus Areas |
|-------|-----------|-----------------|-------------|
| **Backend API** | pytest + TestClient | 95%+ | Authentication, GraphQL resolvers, WebSocket handling |
| **Frontend Components** | Jest + React Testing Library | 90%+ | Canvas interactions, real-time updates, UI controls |
| **Integration** | pytest + WebSocket testing | 85%+ | End-to-end encryption, collaborative sync |
| **E2E** | Cypress | 80%+ | User workflows, multi-user collaboration |

### Test Categories

1. **Unit Tests**: Individual functions and components
2. **Integration Tests**: API endpoints, database operations, WebSocket connections
3. **Security Tests**: Encryption/decryption, authentication flows, input validation
4. **Performance Tests**: Drawing latency, concurrent user limits, memory usage
5. **E2E Tests**: Complete user workflows across multiple browsers

## 🚀 Development Setup

### Prerequisites

- **Docker & Docker Compose** (recommended for full environment)
- **Node.js 18+** & **npm** (frontend development)
- **Python 3.11+** (backend development)
- **FFmpeg** (export functionality)
- **Git** (version control)

### Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/your-username/collab-drawing-board.git
cd collab-drawing-board

# Start all services with Docker Compose
docker-compose up --build

# Access the application
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "GraphQL Playground: http://localhost:8000/graphql"
echo "API Documentation: http://localhost:8000/docs"
```

### Local Development (Advanced)

#### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/drawing"
export REDIS_URL="redis://localhost:6379"
export SECRET_KEY="your-secret-key-here"

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
echo "REACT_APP_WS_URL=ws://localhost:8000/ws" >> .env.local

# Start development server
npm start
```

### Testing Commands

```bash
# Backend tests with coverage
cd backend
pytest --cov=app --cov-report=html --cov-report=term

# Frontend tests with coverage
cd frontend
npm test -- --coverage --watchAll=false

# E2E tests
cd frontend
npx cypress run

# Run all tests (from root directory)
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## 📋 TDD Development Roadmap

### Phase 1: Foundation & Authentication ✅
- [x] Project skeleton with Docker Compose
- [x] PostgreSQL database setup
- [x] JWT authentication system
- [x] User registration and login
- [x] Basic test infrastructure

### Phase 2: Core Drawing Features 🔄
- [ ] Canvas component with Konva.js
- [ ] Pen size and color controls
- [ ] Drawing stroke capture and rendering
- [ ] WebSocket connection setup
- [ ] Real-time stroke broadcasting

### Phase 3: End-to-End Encryption 📋
- [ ] AES-GCM encryption utilities
- [ ] Client-side stroke encryption
- [ ] Secure key management
- [ ] Encrypted stroke storage
- [ ] Decryption for rendering

### Phase 4: Collaboration Features 📋
- [ ] Yjs CRDT integration
- [ ] Multi-user cursor awareness
- [ ] Conflict-free collaborative editing
- [ ] Undo/redo functionality
- [ ] Board clear synchronization

### Phase 5: Persistence & Gallery 📋
- [ ] Stroke persistence to database
- [ ] Board loading and replay
- [ ] PNG export functionality
- [ ] WebM animation export
- [ ] Gallery page with user boards

### Phase 6: Production Polish 📋
- [ ] Performance optimization
- [ ] Security audit and hardening
- [ ] Comprehensive error handling
- [ ] Production deployment configuration
- [ ] Monitoring and observability

## 🎯 Export Functionality

### Supported Export Formats

- **PNG Images**: High-quality static snapshots of drawing boards
- **WebM Animations**: Smooth playback of entire drawing timeline
- **SVG Vector Graphics**: Scalable vector format (future enhancement)

### FFmpeg Integration

```bash
# Generate WebM animation from PNG sequence
ffmpeg -framerate 30 -pattern_type glob -i 'frames/*.png' \
       -c:v libvpx-vp9 -pix_fmt yuva420p -lossless 1 \
       output.webm
```

## 🔮 Future Enhancements

### Mobile Application Expansion
- **Flutter Mobile App**: Cross-platform mobile client using same FastAPI backend
- **Offline Mode**: Local SQLite caching with sync-when-online
- **Touch Optimizations**: Finger drawing with palm rejection

### Advanced Features
- **WebRTC P2P Mode**: Direct peer-to-peer synchronization for low-latency scenarios
- **AI-Powered Tools**: Color palette suggestions, shape recognition, auto-complete
- **Voice Chat Integration**: Real-time communication during collaborative sessions
- **Advanced Permissions**: Board sharing with view/edit permissions
- **Version History**: Git-like branching and merging for drawing boards

### Enterprise Features
- **Single Sign-On (SSO)**: SAML/OAuth integration
- **Audit Logging**: Comprehensive activity tracking
- **Role-Based Access Control**: Granular permission management
- **API Rate Limiting**: DDoS protection and usage quotas
- **Kubernetes Deployment**: Container orchestration for enterprise scale

## 📈 Monitoring & Observability

### Metrics Collection
- **Application Metrics**: Request latency, error rates, concurrent users
- **Drawing Metrics**: Strokes per second, canvas operations, real-time sync delays
- **Infrastructure Metrics**: Database performance, Redis memory usage, WebSocket connections

### Tools Integration (Optional)
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Sentry**: Error tracking and performance monitoring
- **DataDog**: APM and infrastructure monitoring

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Write tests first** (TDD approach)
4. **Implement feature** to pass tests
5. **Run full test suite**: `make test`
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open Pull Request**

### Code Quality Standards
- **100% TDD Coverage**: All new features must have tests written first
- **Type Safety**: Full TypeScript coverage on frontend, mypy on backend
- **Security Review**: All PRs reviewed for security implications
- **Performance Testing**: Latency and load testing for drawing features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Konva.js** - Excellent 2D canvas library
- **Yjs** - Revolutionary CRDT implementation
- **FastAPI** - Modern Python web framework
- **React** - Component-based UI framework
- **Docker** - Containerization platform
- **PostgreSQL** - Robust database system

---

<div align="center">

**Built with ❤️ for real-time collaboration and modern web development**

[🌐 Live Demo](https://your-demo-url.com) • [📖 Documentation](https://your-docs-url.com) • [🐛 Report Bug](https://github.com/your-username/collab-drawing-board/issues) • [💡 Request Feature](https://github.com/your-username/collab-drawing-board/issues)

</div>