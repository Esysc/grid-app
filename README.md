# Grid Monitor v2.0

[![GitHub Pages](https://img.shields.io/badge/demo-live-success?logo=github&style=flat-square)](https://esysc.github.io/grid-app/)
[![Deploy to Pages](https://github.com/Esysc/grid-app/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Esysc/grid-app/actions/workflows/ci-cd.yml)

⚡ A production-grade full-stack grid monitoring and analytics platform with JWT authentication, GraphQL API, real-time S3 export, and interactive SVG-based topology visualization.

## Project Overview

This proof-of-concept showcases a distributed system for monitoring electrical grid infrastructure with:

- **Real-time sensor data processing** from voltage and power quality sensors across the grid
- **Fault detection and alerting** with severity classification (CRITICAL, WARNING, INFO)
- **Power quality analytics** including Total Harmonic Distortion (THD) monitoring
- **Network Logs Panel** for debugging API requests with timing and response details
- **JWT Authentication** for secure API access with OAuth2 password flow
- **GraphQL API** for complex queries and subscriptions (Strawberry)
- **S3 Data Export** with LocalStack integration for testing
- **Interactive Grid Topology Visualization** with SVG-based network diagrams and sensor badges
- **Comprehensive Testing** with pytest (backend) and Vitest (frontend)
- **Live dashboard** with Server-Sent Events (SSE) for real-time metric updates
- **Time-series optimization** using TimescaleDB for efficient sensor data storage
- **MQTT-based sensor simulator** for realistic data injection and fault injection
- **Archive and historical data** exploration with date-based filtering

## Architecture

```shell
┌──────────────────────────┐      ┌──────────────────────────┐      ┌──────────────────┐
│ React 18 Frontend        │◄────►│ FastAPI Backend v2.0     │◄────►│ TimescaleDB      │
│ (Vite + Auth + Viz)      │      │ (REST + GraphQL + SSE)   │      │ (Time-series DB) │
└──────────────────────────┘      └──────────────────────────┘      └──────────────────┘
                                          │          ▲
                                          │          │
                                     ┌────┴──┬───────┴────┐
                                     │       │            │
                                  pgAdmin  LocalStack    MQTT
                                  (Dev)      (S3)      Consumer
                                                            ▲
                                                            │
                                     ┌──────────────────────┴──────────────────┐
                                     │                                         │
                                 Mosquitto MQTT Broker              Sensor Data Generator
                                  (Message Queue)                   (8 Virtual Sensors)
                                                                    OPERATIONAL/FAULTY/
                                                                    RECOVERING States
```

## Tech Stack

| Component | Technology | Version | Status |
| --------- | --------- | ------- | ------ |
| **Backend** | FastAPI | 0.109.0 | ✅ |
| **Language** | Python | 3.12 | ✅ |
| **Frontend** | React | 18.2.0 | ✅ |
| **Build Tool** | Vite | 6.4.1 | ✅ |
| **Charts** | Recharts | 2.10.3 | ✅ |
| **Database** | TimescaleDB | Latest | ✅ |
| **Auth** | JWT (python-jose) | 3.3.0 | ✅ |
| **GraphQL** | Strawberry | 0.220.0+ | ✅ |
| **Cloud Storage** | LocalStack S3 | Latest | ✅ |
| **MQTT** | Mosquitto | 2.0 | ✅ |
| **MQTT Client** | aiomqtt | 2.0.1+ | ✅ |
| **Testing (BE)** | pytest | 7.0+ | ✅ |
| **Testing (FE)** | Vitest | 4.0.16 | ✅ |
| **Containers** | Docker Compose | 3.8+ | ✅ |

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (recommended) or Docker + Docker Compose
- **Git**
- **Node.js 18+** (optional, for local frontend development)
- **Python 3.12** (optional, for local backend development)

### Option 1: Run with Docker Compose (Recommended)

```bash
# Clone and navigate
git clone <your-repo-url>
cd grid-app

# Copy and configure environment
cp .env.example .env

# Start all services (database, backend, frontend, MQTT, S3, pgAdmin)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Clean up (remove volumes)
docker-compose down -v
```

### Option 2: Run Frontend + Backend Locally

**Terminal 1 - Backend:**

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev
```

The frontend will be available at `http://localhost:5173` (Vite default) and configured to proxy API calls to `http://localhost:8000`.

### Access Points

| Service | URL | Notes |
| --------- | ----- | ------------- |
| **Frontend Dashboard** | <http://localhost:3000> (Docker) or <http://localhost:5173> (local) | Demo/test credentials: admin/secret |
| **API Documentation** | <http://localhost:8000/docs> | Interactive Swagger UI with auth token input |
| **GraphQL Playground** | <http://localhost:8000/graphql> | GraphQL IDE with schema explorer |
| **pgAdmin** | <http://localhost:5050> | Database admin (Docker only) |
| **LocalStack S3** | <http://localhost:4566> | S3 API endpoint (Docker only) |
| **MQTT Broker** | localhost:1883 | MQTT protocol (Docker only) |

## 📊 Dashboard Features

### 🔌 Grid Topology & Sensor Network (NEW)

- **Interactive SVG visualization** of electrical grid infrastructure
- **Node types**: Substations (green), Transformers (yellow), Feeders (cyan), Main Hub (red)
- **Real-time sensor badges** showing voltage readings on each node
- **Color-coded status**: Green = operational, Red = faulty, Yellow = warning
- **Clickable nodes** to view all sensors at that location with sensor details modal
- **Multi-sensor modal** with tabs to switch between voltage and power quality sensors
- **Connection mapping** showing electrical relationships between infrastructure components

### 📊 Grid Statistics (Top Cards)

- **Sensors Status**: Operational/Total count with percentage indicator
- **Total Faults (24h)**: Recent fault event count with severity breakdown
- **Power Quality Violations**: THD and harmonic distortion anomalies detected
- **Average Voltage**: Real-time voltage reading across the network
- **Power Factor**: Current power factor with status indicator

### ⚡ Voltage Monitoring Chart

- Real-time voltage trend chart (L1, L2, L3 phases)
- Time-series visualization with 24-hour historical data
- Voltage deviation indicators (±5% from nominal 230V)
- Interactive chart with hover tooltips

### 🔧 Power Quality Chart

- Total Harmonic Distortion (THD) trend analysis
- Individual harmonic component tracking
- Quality violations and anomalies highlighted
- Time-range filtering and zoom capabilities

### ⚠️ Recent Faults Timeline

- Fault event list with timestamps and severity badges
- CRITICAL (red), WARNING (yellow), INFO (blue) severity levels
- Sensor ID and fault description for each event
- Real-time updates via SSE integration
- Scroll to view up to 20 most recent faults

### 📝 Active Sensors List

- Complete sensor inventory with operational status
- Voltage sensors (VS-001 to VS-004) with real-time voltage readings
- Power quality sensors (PQ-001 to PQ-004) with status
- Last update timestamp for each sensor
- Color-coded operational status

### 💾 Export & Archive Features

- **Export Menu**:
  - Export voltage data as JSON (last 24 hours)
  - Export faults as CSV with detailed metadata
  - Export to S3 with LocalStack integration
  - Download exported files directly

- **Archives View**:
  - Browse historical data by date
  - View exported files and metadata
  - Download previous exports
  - Date-based filtering for data exploration

### Core Features (v2.0)

- **Real-time Monitoring**: Live voltage and power quality tracking via SSE
- **Fault Detection**: Automatic severity classification and alerting
- **Analytics Dashboard**: KPI cards, trend charts, and metrics
- **Authentication**: Secure JWT-based API access with login/logout
- **GraphQL Support**: Type-safe queries for advanced data exploration
- **API Toggle**: Switch between REST and GraphQL APIs seamlessly from the UI
- **Data Export**: S3 integration for archival and compliance
- **Time-series Optimization**: TimescaleDB for efficient historical queries
- **MQTT Integration**: Real-time sensor data injection with simulator
- **Responsive UI**: Mobile-friendly React dashboard with Vite

### 🔄 REST/GraphQL API Toggle (NEW)

The frontend now supports switching between REST API and GraphQL API modes without requiring code changes or page reloads:

- **Toggle Switch**: Located in the header next to the navigation tabs
- **Seamless Switching**: Click the toggle button to switch between REST and GraphQL
- **Persistent Preference**: Your API choice is saved in localStorage
- **Unified Interface**: Both APIs return identical data structures to components
- **Real-time Updates**: Data is automatically refetched when switching modes
- **Status Indicator**: Shows current API mode (REST or GraphQL)

**How it works:**
- The `DataFetcher` abstraction layer provides a unified interface for both REST and GraphQL
- GraphQL responses are automatically transformed to match the REST API format
- No changes needed to React components - they receive the same data structure
- Perfect for testing, comparing performance, or choosing your preferred API style

### 🌐 Network Logs Panel (NEW)

Real-time network debugging panel for monitoring all API requests and responses:

- **Collapsible Panel**: Fixed at the bottom of the screen, click to expand/collapse
- **Request Timeline**: All HTTP/GraphQL requests with timestamps and duration
- **Color-Coded Methods**: GET (blue), POST (green), GraphQL (pink)
- **Status Indicators**: Success (✓ green), Error (✗ red), Pending (⋯ orange)
- **Request Details**: Click any log entry to view full request/response payload
- **Performance Monitoring**: Response times displayed in milliseconds
- **Error Debugging**: Full error messages and stack traces for failed requests
- **Request History**: Keeps last 100 requests for analysis
- **Mode Switching**: Logs clear when switching between REST and GraphQL modes
- **Production Ready**: Only visible in non-demo mode for debugging

**Features:**
- JSON syntax highlighting for request/response bodies
- Scrollable detail views with formatted JSON
- Filter by request status (success/error)
- Timestamp with millisecond precision
- Automatic log rotation (last 100 requests)

## 🔐 Security & Authentication

### Login Flow

All data endpoints require JWT authentication. The application uses OAuth2 password flow:

```bash
# 1. Login to get access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

# Response:
# {"access_token": "eyJ0eXAiOiJKV1QiLC...", "token_type": "bearer"}

# 2. Use token in subsequent requests
curl http://localhost:8000/api/sensors/voltage \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLC..."

# 3. Get current user info (requires token)
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLC..."
```

### Frontend Authentication

The React app handles authentication automatically:

- Stores JWT token in localStorage after login
- Includes token in all API request headers
- Redirects to login page if token is invalid or expired
- Supports demo mode (no auth required) for GitHub Pages deployment

### Security Best Practices

- **Demo Credentials** (development only): Username `admin`, Password `secret`
- **Production**: Never use demo credentials—generate strong, unique credentials
- **Token Expiration**: Configure via `JWT_EXPIRATION_HOURS` environment variable
- **Secret Key**: Use 32+ character random string, rotate regularly
- **HTTPS**: Required in production to protect tokens in transit
- **Token Storage**: Currently using localStorage (consider sessionStorage for higher security)

## 📈 API Endpoints

### Authentication (No Auth Required)

```shell
POST   /auth/login              # Login with username/password
GET    /auth/me                 # Get current user profile (requires token)
```

### Sensor Data (Requires Auth)

```shell
GET    /api/sensors/voltage           # Voltage readings (query: sensor_id, limit, hours)
GET    /api/sensors/power-quality     # Power quality metrics (query: sensor_id, limit)
GET    /api/sensors/status            # Current sensor operational status
```

### Faults (Requires Auth)

```shell
GET    /api/faults/recent             # Recent fault events (query: hours, severity, limit)
GET    /api/faults/timeline           # Historical faults with date range filtering
GET    /api/faults/{fault_id}         # Get details of specific fault
```

### Statistics & Monitoring (Requires Auth)

```shell
GET    /api/stats                     # Dashboard statistics (sensors, faults, violations)
GET    /api/stream/updates            # Server-Sent Events stream for real-time updates
```

### Data Export (Requires Auth)

```shell
POST   /api/export/voltage            # Export voltage data (params: hours, format)
POST   /api/export/faults             # Export fault data (params: hours, severity)
GET    /api/export/list               # List all previously exported files
GET    /api/export/download/{file_id} # Download exported file
```

### GraphQL (Requires Auth)

```shell
POST   /graphql                       # Execute GraphQL queries and mutations
GET    /graphql                       # GraphQL Playground IDE
```

### Health & Development

```shell
GET    /                              # API information and version
GET    /health                        # Health check / readiness probe
POST   /api/simulate/populate         # Populate test data (development only)
```

### Supported Query Parameters

| Endpoint | Parameters | Notes |
| -------- | ---------- | ----- |
| `/api/sensors/voltage` | `sensor_id`, `limit` (default: 100), `hours` (default: 24) | Returns voltage readings L1, L2, L3 |
| `/api/sensors/power-quality` | `sensor_id`, `limit` | Returns THD and harmonic data |
| `/api/faults/recent` | `hours`, `severity`, `limit` | Severity: CRITICAL, WARNING, INFO |
| `/api/export/voltage` | `hours` (default: 24), `format` | Format: json or csv |
| `/api/export/faults` | `hours`, `severity` | Exports as CSV with metadata |

## Development

### Local Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (optional for testing/linting)
pip install -r requirements-dev.txt

# Run development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Backend Testing

```bash
cd backend

# Run all tests
pytest -v

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run tests matching pattern
pytest -k "test_login" -v

# Run integration tests
pytest tests/integration/ -v
```

### Backend Code Quality

```bash
cd backend

# Type checking with mypy
mypy .

# Linting with pylint
pylint *.py

# Format code with black
black .

# Import sorting with isort
isort .

# Security scanning
bandit -r .

# Run all checks
pre-commit run --all-files
```

### Local Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Development server (auto-reload)
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview
```

### Frontend Testing

```bash
cd frontend

# Run tests in watch mode
npm test

# Run tests once (CI mode)
npm test -- --run

# Run with coverage report
npm test -- --coverage --run

# Run specific test file
npm test -- src/components/GridTopology.test.jsx
```

### Code Quality (Frontend)

```bash
# Linting (ESLint configured via Vite)
npm run lint  # if script exists

# Format code with Prettier (if installed)
npm run format

# Type checking with TypeScript
npm run type-check  # if script exists
```

## 🗂️ Project Structure

```shell
grid-app/
├── backend/
│   ├── main.py                      # FastAPI app entry point (REST + GraphQL + SSE)
│   ├── auth.py                      # JWT authentication & password hashing
│   ├── graphql_schema.py            # Strawberry GraphQL type definitions
│   ├── s3_export.py                 # S3 export functionality (LocalStack integration)
│   ├── models.py                    # Pydantic data models & SQLAlchemy ORM
│   ├── database.py                  # Database connection & session management
│   ├── data_generator.py            # Simulated sensor data for development/demo
│   ├── Dockerfile                   # Backend container definition
│   ├── requirements.txt              # Python dependencies
│   ├── requirements-dev.txt          # Dev tools (pytest, mypy, etc.)
│   ├── mypy.ini                     # Type checking configuration
│   ├── pytest.ini                   # Pytest configuration
│   ├── tests/
│   │   ├── conftest.py              # Pytest fixtures and configuration
│   │   ├── unit/
│   │   │   ├── test_auth.py         # Authentication tests
│   │   │   ├── test_models.py       # Data model validation tests
│   │   │   ├── test_logic.py        # Business logic tests
│   │   │   └── test_s3_export.py    # S3 export functionality tests
│   │   └── integration/
│   │       ├── test_main.py         # API endpoint integration tests
│   │       ├── test_graphql.py      # GraphQL query tests
│   │       ├── test_api.py          # REST API tests
│   │       ├── test_export_endpoints.py  # Export endpoint tests
│   │       └── test_sse.py          # Server-Sent Events tests
│   └── __pycache__/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Main app component with auth flow & routing
│   │   ├── App.css                  # Global styling & layout
│   │   ├── App.test.jsx             # App-level component tests
│   │   ├── index.jsx                # React entry point
│   │   ├── index.css                # Global styles
│   │   ├── setupTests.js            # Test environment setup
│   │   ├── components/
│   │   │   ├── GridTopology.jsx     # SVG-based topology visualization
│   │   │   ├── GridTopology.css     # Topology styling (fullwidth, centered)
│   │   │   ├── GridTopology.test.jsx # Topology component tests
│   │   │   ├── GridStats.jsx        # Statistics cards component
│   │   │   ├── GridStats.css        # Stats styling
│   │   │   ├── PowerQualityChart.jsx # THD & harmonic distortion chart
│   │   │   ├── FaultTimeline.jsx    # Fault events list component
│   │   │   ├── FaultTimeline.css    # Fault timeline styling
│   │   │   ├── ExportMenu.jsx       # Data export interface
│   │   │   ├── ExportMenu.css       # Export menu styling
│   │   │   ├── ExportMenu.test.jsx  # Export menu tests
│   │   │   ├── Archives.jsx         # Historical data exploration
│   │   │   ├── Archives.css         # Archives styling
│   │   │   ├── Archives.test.jsx    # Archives tests
│   │   │   ├── DemoBanner.jsx       # Demo mode banner
│   │   │   ├── DemoBanner.css       # Banner styling
│   │   │   ├── DemoDataButton.jsx   # Demo data generation
│   │   │   └── DemoDataButton.css   # Button styling
│   │   └── public/
│   ├── index.html                   # HTML template
│   ├── package.json                 # Node.js dependencies & scripts
│   ├── vite.config.js               # Vite configuration with API proxy
│   ├── vitest.config.js             # Vitest test runner configuration
│   ├── Dockerfile                   # Frontend container (Nginx)
│   ├── nginx.conf                   # Nginx configuration for frontend
│   └── coverage/                    # Test coverage reports (generated)
│
├── mqtt/
│   └── sensor_simulator.py          # MQTT sensor data generator (external service)
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml                # GitHub Actions CI/CD pipeline
│
├── docker-compose.yml               # Multi-container orchestration
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── .pre-commit-config.yaml          # Pre-commit hooks for code quality
├── .mypy.ini                        # MyPy type checking configuration
├── ELECTRICAL_METRICS_REFERENCE.md  # Electrical metrics documentation
├── README.md                        # This file
└── test-mqtt.sh                     # MQTT testing script
```

## 🧪 Testing

### Run All Tests

```bash
# Backend tests - all test suites
cd backend && pytest -v

# Backend tests - specific file
cd backend && pytest tests/unit/test_auth.py -v

# Backend tests - with coverage
cd backend && pytest --cov=. --cov-report=html

# Frontend tests - watch mode (interactive)
cd frontend && npm test

# Frontend tests - single run with coverage
cd frontend && npm test -- --coverage --run
```

### Test Coverage

**Backend (pytest):**

- Unit tests: Data models, authentication, password hashing, business logic
- Integration tests: API endpoints, GraphQL queries, S3 export, SSE streams
- Coverage: Aim for 80%+ on critical paths
- Test files located in `backend/tests/unit/` and `backend/tests/integration/`

**Frontend (Vitest):**

- Component tests: Rendering, user interactions, state management
- Integration tests: API calls, authentication flow, data display
- Coverage: Currently 64.7% statements, 48.61% branches
- Test files: `src/**/*.test.jsx` files alongside components

### Continuous Integration

GitHub Actions pipeline (`.github/workflows/ci-cd.yml`) runs:

- Backend: pytest with type checking (mypy)
- Frontend: npm test with coverage report
- Linting: Pre-commit hooks (black, isort, pylint, ESLint)
- Build: Docker image build verification

## Deployment

### Docker Compose (Recommended for Local & Development)

```bash
# Build all images
docker-compose build

# Run all services in detached mode
docker-compose up -d

# View logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Clean up: remove volumes and orphaned containers
docker-compose down -v --remove-orphans
```

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

**Database Configuration:**

```shell
POSTGRES_USER=griduser              # Database user (default: griduser)
POSTGRES_PASSWORD=<secure-password> # Strong password for production
POSTGRES_DB=grid_monitoring         # Database name
DATABASE_URL=postgresql+asyncpg://griduser:password@timescaledb:5432/grid_monitoring
```

**Application Security:**

```shell
JWT_SECRET_KEY=<32-char-random-key>  # Generate: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_ALGORITHM=HS256                  # JWT signing algorithm
JWT_EXPIRATION_HOURS=24              # Token expiration time
PYTHONUNBUFFERABLE=1                 # Enable unbuffered Python output
```

**MQTT Configuration:**

```shell
MQTT_HOST=mosquitto                  # MQTT broker host (Docker) or localhost
MQTT_PORT=1883                       # MQTT port
MQTT_TOPIC=grid/sensors/#           # Topic pattern for sensors
```

**S3/LocalStack (Development):**

```shell
S3_ENDPOINT=http://localhost:4566    # LocalStack S3 endpoint
S3_BUCKET=grid-monitor-exports       # S3 bucket name
S3_ACCESS_KEY=test                   # LocalStack test credentials
S3_SECRET_KEY=test
```

**⚠️ IMPORTANT**:

- Never commit `.env` to version control (included in `.gitignore`)
- For production, use strong random passwords and secrets
- Rotate JWT_SECRET_KEY regularly
- Store secrets in environment management tools (AWS Secrets Manager, HashiCorp Vault, etc.)

### Production Considerations

- Use strong, randomly-generated passwords for database and JWT
- Enable HTTPS/TLS for API endpoints
- Configure proper CORS headers for frontend domain
- Use environment-specific configuration files
- Enable logging and monitoring (ELK stack, Prometheus, etc.)
- Implement rate limiting on API endpoints
- Use database backups and replication
- Monitor disk space and database performance
- Keep dependencies updated for security patches

## 📚 Documentation & Resources

### Live API Documentation

- [**API Documentation (Swagger UI)**](http://localhost:8000/docs) - Interactive API documentation (after starting backend)
- [**GraphQL Playground**](http://localhost:8000/graphql) - GraphQL IDE with schema introspection (after starting backend)

### Reference Documentation

- [**Electrical Metrics Reference**](ELECTRICAL_METRICS_REFERENCE.md) - Grid monitoring terminology, voltage standards, power quality metrics, and harmonic analysis

### External Resources

- **GitHub Repository**: <https://github.com/Esysc/grid-app>
- **Live Demo**: <https://esysc.github.io/grid-app/>
- **Issues & Discussions**: GitHub Issues tab

## 🤝 Contributing

### Getting Started

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes with tests
5. Ensure all tests pass: `pytest` (backend) and `npm test` (frontend)
6. Run code quality checks: `pre-commit run --all-files`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Submit a pull request with a clear description

### Code Style & Standards

**Python:**

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Format code with `black`
- Sort imports with `isort`
- Lint with `pylint` and type-check with `mypy`

**JavaScript/JSX:**

- Use ES6+ syntax and features
- Follow React best practices
- Use functional components with hooks
- Write tests for all components
- Format code with Prettier (if configured)

**Git Workflow:**

- Use descriptive commit messages
- Reference issues in commit messages (e.g., "Fixes #123")
- Keep commits focused on a single feature/fix
- Rebase before submitting pull request

### Testing Requirements

- All new features must include tests
- Backend: Aim for 80%+ coverage on new code
- Frontend: Component tests required for user-facing features
- Run `pytest` and `npm test` before submitting PR

### Pull Request Process

1. Update documentation for any new features
2. Add/update tests as needed
3. Ensure CI/CD pipeline passes
4. Request reviews from maintainers
5. Address review comments
6. Squash commits if requested
7. Merge when approved

## ⚙️ Configuration Reference

### Database (TimescaleDB)

| Setting | Default | Notes |
| ------- | ------- | ----- |
| **Host** | timescaledb | Docker service name (localhost for local dev) |
| **Port** | 5432 | PostgreSQL standard port |
| **User** | griduser | Set via POSTGRES_USER env var |
| **Password** | *(required)* | Set via POSTGRES_PASSWORD env var - use strong password in production |
| **Database** | grid_monitoring | Set via POSTGRES_DB env var |
| **Connection Pool** | 10 | Min/max connections for asyncpg |
| **SSL Mode** | disable | Set to `require` in production |

### JWT Authentication

| Setting | Default | Notes |
| ------- | ------- | ----- |
| **Algorithm** | HS256 | HMAC SHA256 signing |
| **Secret Key** | *(required)* | 32+ character random string |
| **Expiration** | 24 hours | Can be configured per environment |
| **Refresh Token** | Not implemented | Future enhancement |

### MQTT Broker (Mosquitto)

| Setting | Default | Notes |
| ------- | ------- | ----- |
| **Host** | mosquitto | Docker service name (localhost for local) |
| **Port** | 1883 | Standard MQTT port |
| **Topic Pattern** | grid/sensors/# | Hierarchical topic structure |
| **QoS** | 1 | At-least-once delivery guarantee |
| **Retained Messages** | Enabled | Last message retained for new subscribers |

### S3 / LocalStack

| Setting | Default | Notes |
| ------- | ------- | ----- |
| **Endpoint** | <http://localhost:4566> | LocalStack S3 endpoint |
| **Region** | us-east-1 | AWS region setting |
| **Bucket** | grid-monitor-exports | S3 bucket for file exports |
| **Access Key** | test | LocalStack demo credentials |
| **Secret Key** | test | Change for production |
| **Signature Version** | s3v4 | AWS signature algorithm |

### Application Settings

| Setting | Default | Notes |
| ------- | ------- | ----- |
| **API Host** | 0.0.0.0 | Bind to all interfaces |
| **API Port** | 8000 | FastAPI server port |
| **Frontend Port** | 3000 (Docker) / 5173 (Vite dev) | Development server port |
| **Log Level** | INFO | DEBUG/INFO/WARNING/ERROR |
| **CORS Origins** | * | Restrict in production |
| **HTTPS** | Disabled | Enable in production |

### Sensor Configuration

| Sensor Type | ID Range | Count | Sampling Rate |
| ----------- | --------- | ----- | ------------- |
| **Voltage Sensors** | VS-001 to VS-004 | 4 | 1 Hz (1 second) |
| **Power Quality Sensors** | PQ-001 to PQ-004 | 4 | 1 Hz (1 second) |
| **Total** | - | 8 | 1 Hz |

## 📄 License

This project is provided as-is for demonstration and educational purposes.

**Note:** Some icons and assets may be subject to their respective licenses. Please review individual component licenses if using in production.

## 🆘 Troubleshooting

### Common Issues

**Problem**: Docker containers won't start

```bash
# Solution: Check port conflicts
lsof -i :8000  # Check port 8000
lsof -i :5432  # Check port 5432
docker-compose down -v  # Clean up
docker-compose up -d --no-cache  # Rebuild
```

**Problem**: Frontend can't connect to backend

```bash
# Check proxy configuration in frontend/vite.config.js
# For Docker: target should be 'http://backend:8000'
# For local dev: target should be 'http://localhost:8000'
```

**Problem**: Database connection error

```bash
# Verify database is running
docker-compose logs timescaledb

# Check database credentials in .env
cat .env | grep POSTGRES

# Reset database
docker-compose down -v
docker-compose up -d timescaledb
sleep 10  # Wait for initialization
```

**Problem**: JWT authentication failing

```bash
# Verify JWT_SECRET_KEY is set
echo $JWT_SECRET_KEY

# Check token in browser console
localStorage.getItem('accessToken')

# Re-login to get new token
```

**Problem**: MQTT sensor data not appearing

```bash
# Check MQTT broker
docker-compose logs mosquitto

# Check sensor simulator
docker-compose logs backend

# Verify MQTT connectivity
mosquitto_sub -h localhost -t "grid/sensors/#"
```

### Getting Help

- Review GitHub Issues for similar problems
- Check application logs: `docker-compose logs`
- Read API documentation at <http://localhost:8000/docs> (start backend first)
- Check [Electrical Metrics Reference](ELECTRICAL_METRICS_REFERENCE.md) for grid terminology

## 📝 Version History

### v2.0.0 (Current)

✨ **Major Release** - Production-Ready Features

**New Features:**

- JWT authentication with OAuth2 password flow
- GraphQL API with Strawberry implementation
- S3 data export with LocalStack integration
- Interactive SVG-based topology visualization with sensor badges
- MQTT-based sensor simulator with state machine
- Comprehensive pytest unit and integration tests
- Vitest for React component testing
- Server-Sent Events (SSE) for real-time updates
- Archive and historical data exploration
- Export menu with CSV/JSON formats
- Grid statistics KPI dashboard cards

**Improvements:**

- Fullwidth grid topology layout optimization
- Centered topology visualization with responsive design
- Enhanced error handling and validation
- Type hints throughout Python codebase
- Pre-commit hooks for code quality
- GitHub Actions CI/CD pipeline
- Improved documentation and API references

**Breaking Changes:**

- Frontend routing changed (Dashboard, Archives, Logout views)
- API endpoints now require JWT authentication
- Database schema optimized for TimescaleDB

### v1.0.0 (Initial Release)

- REST API with real-time monitoring
- React dashboard with charts
- Basic fault detection
- PostgreSQL time-series storage
