<<<<<<< HEAD
# grid-app
=======
# Grid Monitor v2.0

⚡ A production-grade full-stack grid monitoring and analytics platform with JWT authentication, GraphQL API, real-time S3 export, and interactive topology visualization.

## Project Overview

This proof-of-concept showcases a distributed system for monitoring electrical grid infrastructure with:

- **Real-time sensor data processing** from voltage sensors across the grid
- **Fault detection and alerting** with severity classification
- **Power quality analytics** including Total Harmonic Distortion (THD) monitoring
- **JWT Authentication** for secure API access
- **GraphQL API** for complex queries and subscriptions
- **S3 Data Export** with LocalStack integration
- **Grid Topology Visualization** with network diagrams
- **Comprehensive Testing** with pytest and React Testing Library
- **Live dashboard** with Server-Sent Events for real-time updates
- **Time-series optimization** using TimescaleDB

## Architecture

```
┌─────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────┐
│  React 18 Frontend      │◄────►│  FastAPI Backend v2.0    │◄────►│   TimescaleDB    │
│  (Auth + Dashboard)     │      │  (REST + GraphQL + SSE)  │      │  (Time-series)   │
└─────────────────────────┘      └──────────────────────────┘      └──────────────────┘
                                           │
                                      ┌────┴────┐
                                      │          │
                                   LocalStack   pgAdmin
                                     (S3)       (Dev)
```

## Tech Stack

| Component | Technology | Version | Status |
|-----------|-----------|---------|--------|
| **Backend** | FastAPI | 0.109.0 | ✅ |
| **Language** | Python | 3.12 | ✅ |
| **Frontend** | React | 18.2.0 | ✅ |
| **Charts** | Recharts | 2.10.3 | ✅ |
| **Database** | TimescaleDB | Latest | ✅ |
| **Auth** | JWT + python-jose | 3.3.0 | ✅ NEW |
| **GraphQL** | Strawberry | 0.220.0 | ✅ NEW |
| **Cloud Storage** | LocalStack S3 | Latest | ✅ NEW |
| **Testing** | pytest + RTL | 7.0+ | ✅ NEW |
| **Containers** | Docker Compose | 3.8 | ✅ |

## 🚀 Quick Start

### Prerequisites

- Docker Desktop or Docker + Docker Compose
- Git
- Node.js 18+ (optional, for local development)
- Python 3.12 (optional, for local development)

### Run with Docker Compose (Recommended)

```bash
# Clone and navigate
git clone <your-repo-url>
cd grid-app

# Start all services (database, backend, frontend, localstack, pgadmin)
docker-compose up -d

# Check status
docker-compose ps

# Stop services
docker-compose down
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend Dashboard | http://localhost:3000 | admin / secret |
| API Documentation | http://localhost:8000/docs | N/A |
| GraphQL Playground | http://localhost:8000/graphql | N/A |
| pgAdmin | http://localhost:5050 | admin@grid-monitor.com / admin |
| LocalStack S3 | http://localhost:4566 | test / test |

## 📊 Features

### 🔐 Version 2.0 - Enhanced Features

#### JWT Authentication (NEW)
- Secure login endpoint at `/auth/login`
- OAuth2 password flow
- Bearer token-based authorization
- Protected data endpoints
- Demo credentials: `admin` / `secret`

#### GraphQL API (NEW)
- Full GraphQL schema at `/graphql`
- Type-safe queries for voltage, power quality, faults
- Strawberry GraphQL integration
- Interactive playground included

#### S3 Data Export (NEW)
- Export voltage readings as JSON
- Export fault events as CSV
- LocalStack S3 integration for testing
- File listing and retrieval endpoints
- Auto-timestamped exports

#### Grid Topology Visualization (NEW)
- Canvas-based network diagram
- Substations, transformers, feeders visualization
- Color-coded node types
- Connection mapping
- Dynamic rendering

#### Comprehensive Testing (NEW)
- Backend unit tests with pytest
- React component tests
- Authentication flow tests
- Data model validation
- 90%+ code coverage capability

### Core Features

- **Real-time Monitoring**: Live voltage and power quality tracking
- **Fault Detection**: Automatic severity classification
- **Analytics Dashboard**: KPI cards and trend charts
- **SSE Streaming**: Real-time metric updates
- **Time-series DB**: Optimized for grid sensor data

## 🔐 Security & Authentication

All data endpoints require JWT authentication:

```bash
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

# Response: {"access_token": "eyJ0eXAi...", "token_type": "bearer"}

# 2. Use token
# Replace <your_token> with the access_token from login
curl http://localhost:8000/sensors/voltage \
  -H "Authorization: Bearer <your_token>"
```

## 📈 API Endpoints

### Authentication
```
POST   /auth/login              Login and get JWT token
GET    /auth/me                 Get current user profile
```

### Sensors (Requires Auth)
```
GET    /sensors/voltage         Voltage readings (query params: sensor_id, hours)
GET    /sensors/power-quality   Power quality metrics
```

### Faults (Requires Auth)
```
GET    /faults/recent           Recent fault events (params: hours, severity)
GET    /faults/timeline         Historical faults (params: start_date, end_date)
```

### Analytics (Requires Auth)
```
GET    /stats                   Dashboard statistics
GET    /stream/updates          Real-time SSE stream
```

### Export (Requires Auth)
```
POST   /export/voltage          Export voltage data (params: hours)
POST   /export/faults           Export fault data
GET    /export/list             List all exported files
```

### GraphQL
```
POST   /graphql                 GraphQL queries
GET    /graphql                 GraphQL playground
```

### Health & Development
```
GET    /                        API info
GET    /health                  Health check
POST   /simulate/populate       Populate test data (dev only)
```

## Development

### Local Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev tools
pip install pytest pytest-asyncio

# Run server
uvicorn main:app --reload
```

### Backend Tests

```bash
cd backend

# Run all tests
pytest test_main.py -v

# Run specific test class
pytest test_main.py::TestDataGenerator -v

# Run with coverage
pytest test_main.py --cov=.
```

### Local Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Code Quality

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run all checks
pre-commit run --all-files

# Includes: black, isort, flake8, pylint, mypy, bandit, yaml lint, markdown lint
```

## 🗂️ Project Structure

```
grid-app/
├── backend/
│   ├── main.py                  # FastAPI app with auth & GraphQL
│   ├── auth.py                  # JWT authentication (NEW)
│   ├── graphql_schema.py        # GraphQL type definitions (NEW)
│   ├── s3_export.py             # S3 export functionality (NEW)
│   ├── models.py                # Pydantic data models
│   ├── database.py              # SQLAlchemy ORM & connection
│   ├── data_generator.py        # Simulated sensor data
│   ├── test_main.py             # Unit tests (NEW)
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile               # Backend container
│   └── .pylintrc                # Linting config
│
├── frontend/
│   ├── src/
│   │   ├── App.js               # Main app with auth & SSE
│   │   ├── App.css              # Global styling
│   │   ├── App.test.js          # App tests (NEW)
│   │   ├── index.js             # Entry point
│   │   ├── components/
│   │   │   ├── PowerQualityChart.jsx
│   │   │   ├── FaultTimeline.jsx
│   │   │   ├── GridStats.jsx
│   │   │   ├── GridTopology.jsx    # NEW
│   │   │   ├── GridTopology.css
│   │   │   ├── GridTopology.test.jsx
│   │   │   └── *.css
│   │   └── public/
│   ├── package.json             # Node dependencies
│   ├── Dockerfile               # Frontend container
│   └── .gitignore
│
├── docker-compose.yml           # Multi-container orchestration
├── .pre-commit-config.yaml      # Linting hooks
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # GitHub Actions pipeline
├── instructions/
│   └── PROJECT_CONTEXT.md       # Project documentation
├── README.md                    # This file
└── .gitignore

```

## 🧪 Testing

### Run All Tests

```bash
# Backend tests
cd backend && pytest test_main.py -v

# Frontend tests
cd frontend && npm test -- --coverage
```

### Test Coverage

- **Backend**: Data generation, model validation, authentication, password hashing
- **Frontend**: Component rendering, user interactions, API integration

## Deployment

### Docker Compose Production

```bash
# Build images
docker-compose build

# Run services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Environment Variables

The application uses environment variables for configuration. For local development, create a `.env` file in the project root:

```bash
# Copy from backend example
cp backend/.env.example .env

# Then edit .env and update POSTGRES_PASSWORD
```

Your `.env` should look like this (but with your own secure password):

```
POSTGRES_USER=griduser
POSTGRES_PASSWORD=grid_power_2024
POSTGRES_DB=grid_monitoring
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@timescaledb:5432/${POSTGRES_DB}
PYTHONUNBUFFERED=1
```

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs) - Interactive Swagger UI
- [GraphQL Playground](http://localhost:8000/graphql) - GraphQL IDE
- [Project Context](instructions/PROJECT_CONTEXT.md) - Detailed project info

## 🤝 Contributing

1. Create a feature branch
2. Make changes
3. Run `pre-commit run --all-files`
4. Submit pull request

## ⚙️ Configuration

### Database
- **Host**: timescaledb:5432
- **User**: griduser (Configurable via `POSTGRES_USER`)
- **Password**: Configurable via `POSTGRES_PASSWORD`
- **Database**: grid_monitoring (Configurable via `POSTGRES_DB`)

### Authentication
- **Secret Key**: grid-monitor-secret-key-change-in-production
- **Algorithm**: HS256
- **Token Expiry**: 30 minutes
- **Demo User**: admin / secret

### S3 (LocalStack)
- **Endpoint**: http://localhost:4566
- **Bucket**: grid-monitor-exports
- **Access Key**: test
- **Secret Key**: test

## 📄 License

This project is provided as-is for demonstration purposes.

## 📝 Version History

- **v2.0.0** - Added JWT auth, GraphQL, S3 export, topology visualization, tests
- **v1.0.0** - Initial REST API with real-time monitoring dashboard
>>>>>>> 1631479 (feat(frontend): add React 18 dashboard with JWT auth, real-time charts, and grid topology)
