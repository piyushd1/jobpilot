# JobPilot

Autonomous multi-agent job hunting orchestrator. Manager-led DAG orchestration on Temporal with policy-aware job discovery, multi-signal scoring, and human-in-the-loop outreach pipeline.

## Architecture

```
User uploads resume + preferences
        |
   FastAPI Gateway
        |
   Temporal Workflow (Manager Agent)
        |
   +---------+---------+---------+
   |         |         |         |
 Resume    Job Scout  Research  QA/Critic
 Parser    (per platform)  Agent    Agent
   |         |         |         |
   +----+----+---------+---------+
        |
   Dedup + Score + Risk Detection
        |
   Approval Gate (human review)
        |
   Outreach Finder + Draft Generation
        |
   Approval Gate (human review)
        |
   Deliver Results
```

**Core outputs per campaign:**
1. Ranked job shortlist with explainable scores
2. Canonical application links (employer ATS preferred)
3. Prioritized contacts: Hiring Managers > Recruiters > Peers
4. Personalized outreach message drafts
5. Risk flags on suspicious postings

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for frontend)

### 1. Clone and setup

```bash
git clone https://github.com/piyushd1/jobpilot.git
cd jobpilot
python3.11 -m venv .venv
source .venv/bin/activate
make setup
```

This installs all Python dependencies and copies `.env.example` to `.env`.

### 2. Configure environment

Edit `.env` with your API keys:

```bash
# Required for LLM features
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key

# Optional: proxy services (Phase 2+)
BRIGHTDATA_USERNAME=
BRIGHTDATA_PASSWORD=
SERPAPI_KEY=
```

### 3. Start infrastructure services

```bash
make dev
```

This starts PostgreSQL, Redis, Qdrant, MinIO, Temporal server + UI, then runs the FastAPI server at `http://localhost:8000`.

**Service ports:**

| Service | Port | URL |
|---------|------|-----|
| API Server | 8000 | http://localhost:8000 |
| Temporal UI | 8080 | http://localhost:8080 |
| Qdrant | 6333 | http://localhost:6333 |
| MinIO Console | 9001 | http://localhost:9001 |
| PostgreSQL | 5432 | - |
| Redis | 6379 | - |

### 4. Run database migrations

```bash
make migrate
```

### 5. Start the Temporal worker

In a separate terminal:

```bash
source .venv/bin/activate
make worker
```

### 6. Start the frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### 7. Verify everything works

```bash
curl http://localhost:8000/health
# {"status":"ok","environment":"development"}
```

## Running Tests

```bash
# Unit tests only (fast, no external deps)
make test

# All tests (unit + integration + scoring validation)
source .venv/bin/activate
pytest tests/ -v

# With coverage
make test-cov

# Scoring accuracy validation
pytest tests/scoring_validation -v

# Canary health checks
python -m tests.load.canary
```

**Current test suite:** 250 tests passing in <2s.

## Project Structure

```
jobpilot/
+-- src/
|   +-- agents/          # Agent implementations (AgentShell base + workers)
|   |   +-- base.py          # AgentShell ABC: 5-step execution loop
|   |   +-- resume_parser.py # PDF extraction + LLM structured parsing
|   |   +-- qa_critic.py     # Post-pipeline quality assurance checks
|   +-- orchestration/   # Temporal workflow engine
|   |   +-- workflows.py     # JobPilotWorkflow (main campaign workflow)
|   |   +-- activities.py    # Temporal activity wrappers for agents
|   |   +-- dag.py           # TaskDAG with dependency resolution
|   |   +-- shared_context.py
|   |   +-- planner.py       # Campaign DAG builder
|   +-- scoring/         # Multi-signal scoring engine
|   |   +-- engine.py        # 8-signal weighted scorer
|   |   +-- skill_graph.py   # Tech Adjacency Graph (synonyms + adjacency)
|   |   +-- embeddings.py    # Embedding pipeline (Qdrant storage)
|   |   +-- normalizer.py    # Skill synonym normalization
|   |   +-- risk_detector.py # Fraud/scam detection rules
|   +-- platforms/       # Job platform adapters
|   |   +-- base_adapter.py  # PlatformAdapter ABC with strategy cascade
|   |   +-- source_policy.py # Source Capability Registry
|   +-- scraping/        # Web scraping infrastructure
|   |   +-- browser_pool.py  # Playwright pool (ATS pages only)
|   |   +-- proxy_pool.py    # BrightData + SmartProxy rotation
|   |   +-- rate_limiter.py  # Redis token bucket per domain
|   |   +-- session_manager.py
|   +-- services/        # Shared services
|   |   +-- llm_gateway.py   # LiteLLM multi-provider wrapper
|   |   +-- vector_store.py  # Qdrant client
|   |   +-- cache.py         # Redis client
|   |   +-- storage.py       # MinIO object storage
|   |   +-- approval_service.py  # Human-in-the-loop gates
|   |   +-- encryption.py    # PII field encryption
|   |   +-- prompt_guard.py  # Prompt injection detection
|   +-- models/          # Data models
|   |   +-- database.py      # SQLAlchemy ORM (13 tables)
|   |   +-- schemas.py       # Pydantic models
|   |   +-- enums.py         # Shared enums
|   +-- utils/           # Utilities
|   |   +-- logging.py       # Structlog + OpenTelemetry
|   |   +-- metrics.py       # Application metrics
|   |   +-- deduplication.py # 3-stage job dedup pipeline
|   |   +-- canonicalization.py
|   +-- main.py          # FastAPI app entry
|   +-- worker.py        # Temporal worker entry
+-- tests/
|   +-- unit/            # 235 unit tests (no external deps)
|   +-- integration/     # E2E pipeline + Temporal DAG tests
|   +-- scoring_validation/  # Ground truth accuracy tests
|   +-- load/            # Locust load tests + canary runner
|   +-- fixtures/        # Sample JDs, resume fixtures
+-- alembic/             # Database migrations
+-- k8s/                 # Kubernetes manifests
+-- observability/       # Prometheus, alerting, Promtail configs
+-- frontend/            # React + Vite frontend
+-- docker-compose.yml
+-- docker-compose.observability.yml
+-- Dockerfile
+-- pyproject.toml
+-- Makefile
```

## Key Commands

```bash
make dev          # Start infra + API server
make dev-all      # Start everything via Docker Compose
make dev-down     # Stop all services
make dev-reset    # Stop + delete volumes + restart
make worker       # Start Temporal worker
make test         # Run unit tests
make test-cov     # Tests with coverage report
make migrate      # Run DB migrations
make migrate-new  # Create new migration
make lint         # Lint with ruff
make format       # Auto-format code
make typecheck    # Mypy type checking
make clean        # Remove cache files
make setup        # First-time project setup
```

## Observability Stack

Start the full observability stack alongside the main services:

```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d
```

| Tool | Port | Purpose |
|------|------|---------|
| Jaeger UI | 16686 | Distributed tracing |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Dashboards |
| Loki | 3100 | Log aggregation |

### Alerting Rules

- Source success rate < 70% per platform
- LLM API error rate > 5%
- Campaign duration > 4 hours
- Cost per campaign > $5
- High challenge/CAPTCHA encounter rate

## Scoring Engine

The scoring engine evaluates candidate-job fit across 8 weighted signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| Skills Match | 0.30 | Jaccard + adjacency credit + semantic |
| Title Alignment | 0.15 | Embedding cosine or keyword overlap |
| Experience Fit | 0.15 | Range overlap + Gaussian decay |
| Semantic Similarity | 0.10 | Full profile vs JD embedding |
| Company Preference | 0.10 | Exact + partial match |
| Location Fit | 0.08 | Remote / same city / relocation |
| Recency | 0.07 | Exponential decay (14-day half-life) |
| Source Confidence | 0.05 | Platform reliability score |

**Tiers:** STRONG (>=0.80), GOOD (>=0.60), PARTIAL (>=0.40), WEAK (<0.40)

**Conflict arbitration:** If semantic similarity > 0.80 but hard skill overlap < 0.50, tier is capped at GOOD.

## Security

- PII fields encrypted at rest (Fernet/AES)
- Prompt injection detection on all LLM inputs (15 patterns)
- Domain allowlist for browser automation (Lever, Greenhouse, Workday only)
- Policy-enforced source access (no unauthorized scraping)
- Auto-stop on CAPTCHA/challenge detection (no bypass)
- GDPR-compliant data retention and deletion

## Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/hpa.yaml
```

Node pool layout: `general` (API, workers), `browser` (Playwright, seccomp-restricted), `stateful` (databases, managed separately).

## CI/CD

GitHub Actions runs on every push/PR:
1. **Lint** (ruff check + format)
2. **Unit tests** (235 tests, <2s)
3. **Integration tests** (E2E pipeline, DAG ordering)
4. **Scoring validation** (ground truth accuracy)
5. **Type checking** (mypy)
6. **Docker build** (on merge to main)

Weekly scoring accuracy validation runs separately and auto-creates GitHub issues on regression.

## License

MIT
