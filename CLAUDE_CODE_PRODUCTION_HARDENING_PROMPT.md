## Claude Code Prompt: Production Hardening for CoinLink MVP (Backend, WebSockets, Auth, Observability, CI/CD)

### Objective
- Implement system-wide, production-grade changes across backend API, authentication, WebSockets, observability, and CI/CD to make the CoinLink MVP production-ready on Railway.
- Deliver complete, working code with tests. No placeholders, no TODOs. Preserve existing domain modules (Agents, R&D, Growth), but harden for real-world operation.

### Context & Constraints
- **Tech stack**
  - Backend: Python 3.11, FastAPI, Uvicorn (ASGI), WebSockets
  - Data: PostgreSQL (asyncpg), Redis
  - Queues/WS fanout: Redis Pub/Sub
  - Auth: JWT (HS256), BCrypt password hashing (passlib)
  - Config: Pydantic v2 Settings via environment variables
  - Observability: Prometheus metrics, Sentry for errors, structured JSON logging
  - CI/CD: GitHub Actions → GHCR → Railway deploy
  - Frontend: React (Node 20); robust WebSocket client already implemented
- **Environments**
  - Local: Docker Compose with Postgres + Redis
  - Staging/Production: Railway (Linux container), `PORT` injected, possibly multiple workers
- **Codebase layout (relevant)**
  - Backend API: `backend/api/main_production.py`
  - Backend routers: `backend/api/routes/agents.py`, `backend/api/routes/rd_routes.py`, `backend/api/routes/rd_status.py`
  - Auth (to replace/harden): `backend/auth/simple_auth.py`, `backend/auth/auth_api.py`
  - Middleware: `backend/middleware/security.py`, `backend/middleware/cache.py`
  - Config: `backend/config/settings.py`
  - Agents: `backend/agents/*` (includes `orchestrator/helios.py`, `monitoring.py`, `claude_agent_interface.py`, `base.py`)
  - R&D: `backend/rd/*` (scheduler, orchestrator, metrics, pipeline)
  - Growth: `backend/growth/*` (api_routes, metrics, scheduler, notifications)
  - Frontend API client and WS: `frontend/src/services/api.js`, app wiring `frontend/src/App.jsx`
  - Deploy/Infra: `Dockerfile`, `docker-compose.yml`, `Procfile`, `railway.json`, `.github/workflows/parallel-ci.yml`
- **Conventions**
  - Pydantic v2 models, FastAPI async routes, strong typing
  - High-verbosity, readable code; no TODOs or placeholders
  - Maintain existing indentation and formatting; do not reformat unrelated code

### Deliverables (no placeholders)
- Fully implemented code across all tasks below
- Database migrations (Alembic) for new tables
- Unit/integration tests with deterministic outcomes
- Updated CI workflow: tests + security scans + build + deploy
- Updated docs: `README.md`, `RAILWAY_ENV_VARS.md`, `.env.example`

---

## Tasks

### 1) Security & Middleware (mount and enforce)
- Mount security middleware in `backend/api/main_production.py`:
  - `app.state.security_middleware = security_middleware`
  - Register `RequestLoggingMiddleware` and `InputValidationMiddleware` via `app.middleware("http")(...)` (from `backend/middleware/security.py`)
  - Add 429 handler for rate-limit exceedances (SlowAPI/FastAPI-Limiter) with consistent JSON error
- Replace permissive CORS. Use exact allowed origins parsed from CSV env `ALLOWED_ORIGINS`:
  - Set `allow_origins=parsed_list`, `allow_credentials=True`, `allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"]`, `allow_headers=["Authorization","Content-Type","Accept","Origin"]`
- Remove default JWT secret fallback. Startup must fail if `JWT_SECRET_KEY` missing:
  - In `backend/config/settings.py` make `JWT_SECRET_KEY` required; validate all critical env at startup; raise clear error
- Rate limiting backed by Redis:
  - Use `fastapi-limiter` or SlowAPI + Redis storage
  - Defaults: Global 100 req/min per IP; Auth endpoints 10/min; Chat 20/min; Price 60/min; mirror and/or supersede the map in `security.py`
  - Enforce via decorators or centralized path-based rules (do not leave unmounted)

### 2) Authentication: persistent, secure, versioned API
- Replace in-memory auth with production-grade service:
  - Add SQLAlchemy 2.0 async + asyncpg; create `users` table (id UUID, email unique indexed, password_hash, created_at, updated_at)
  - BCrypt hashing (`passlib[bcrypt]`, cost >= 12)
  - JWT access tokens (15m) and refresh tokens (7d) with rotation; HS256; keys from env; include `iss`, `aud` and verify
  - Token blacklist on logout/rotation stored in Redis with TTL matching expiration
- API under `/api/v2/auth` (replace `backend/auth/simple_auth.py` usage):
  - `POST /signup` (email, password) → create user, return access+refresh tokens
  - `POST /login` (email, password) → return tokens
  - `POST /token/refresh` (refresh_token) → returns new access+refresh (rotate, blacklist old refresh)
  - `POST /logout` (refresh_token) → blacklist provided refresh
  - `GET /verify` → validates `Authorization: Bearer <access>` and returns user
  - `GET /rate-limit` → returns remaining window (per IP/user)
- Validation:
  - Email RFC-like regex, max length 254
  - Password: min 12 chars, at least one upper/lower/digit/special; max length 512
  - Reject suspicious inputs (control chars, known injection patterns)
- Error handling: standardized JSON (see “Error schema”) with appropriate HTTP codes: 400, 401, 403, 429, 500
- Include router in `backend/api/main_production.py` with prefix `/api/v2/auth`

### 3) Database & Migrations
- Add `backend/db` module:
  - `database.py` (async engine, sessionmaker, health checker)
  - `models.py` (User model)
  - `repositories.py` (user CRUD)
  - `schemas.py` (pydantic request/response)
- Alembic setup in `backend/alembic` with autogenerated initial migration for `users`
- Health checks:
  - Add `/readyz`: DB connect OK, Redis ping OK, critical env loaded OK → 200, else 503
  - Add `/livez`: simple event loop responsiveness → 200
  - Keep existing low-cost `/health` for quick status

### 4) WebSockets: production fanout + ticker producer
- Background ticker producer:
  - Fetch prices every 5s from configured provider (prefer CoinGecko; support Coinbase if keys present)
  - Normalize data: list of `{symbol, price, change_24h}` for top N (include BTC)
  - On failure: degrade gracefully, reuse last snapshot with `stale=true`, error log
- Multi-worker scaling:
  - Use Redis Pub/Sub channel `ws:ticker` for broadcasts
  - Each worker subscribes and forwards JSON to its connected clients (per-process `ConnectionManager`)
- Message contract:
  - `{ type: "crypto_ticker_update", data: [...], timestamp, stale }`
  - Preserve current `connected` message and ping/pong handling
- Inbound WS protection: rate-limit chat/ping from clients

### 5) Endpoint parity with Frontend
- Implement missing REST endpoints used by `frontend/src/services/api.js`:
  - `GET /api/bitcoin/sentiment` → minimal sentiment (provider if keys; fallback heuristic), JSON shape expected by FE
  - `GET /api/bitcoin/market-summary` → 24h summary
  - `GET /api/bitcoin/news?limit=` → NewsAPI if key; fallback curated list
  - `POST /api/bitcoin/analyze` → analyze text (baseline heuristic or small model), include `model: "baseline"`
  - `GET /api/chat/history` → last N messages (Redis list; anonymous session or authenticated user)
  - `GET /api/prompts` → curated prompts array
- Apply `CacheMiddleware` headers to read-only endpoints
- Fix dev parity in `docker-compose.yml`: use `uvicorn backend.api.main_production:app --reload`

### 6) Observability & Logging
- Prometheus:
  - Add `prometheus_fastapi_instrumentator`; expose `/metrics`
  - Custom metrics: WS connected clients, ticker broadcast count, provider errors, DB pool utilization, limiter events
- Sentry:
  - Initialize with `SENTRY_DSN` if provided; capture exceptions; include release/env tags
- Structured JSON logging:
  - JSON logs with request id, trace id, path, method, status, latency ms, user id (if present)
  - Mask secrets; INFO in prod, DEBUG in staging
- Unified monitoring integration:
  - Expose `/api/monitoring/unified` to return snapshot from `backend/master_orchestrator/unified_monitoring.py`
  - Every 60s feed core metrics into unified monitor instance

### 7) Performance Requirements & SLAs
- SLAs:
  - REST p95 < 150ms, p99 < 400ms (excluding cold start)
  - WS broadcast p95 < 250ms from fetch to client send (single region)
  - Error rate < 1% over 5 minutes
- Optimizations:
  - DB: pool size 10, max overflow 20, statement timeout 2s; index `users.email`
  - Redis: connection pooling, timeouts; pipelines where useful
  - HTTP: keepalive, gzip/deflate; compress larger JSON responses
  - Caching: ETag + Cache-Control (`CacheMiddleware`) for GETs
  - Concurrency: avoid blocking calls; asyncio for network I/O; backoff with jitter for providers
  - Circuit breaker: open after 5 consecutive failures; half-open retry every 30s

### 8) Security Requirements
- JWT:
  - Access (15m), Refresh (7d), rotation, blacklist on logout/refresh reuse
  - Verify `iss`, `aud`; tolerate 60s clock skew
- Password hashing: BCrypt with strength ≥ 12
- Input validation: strict Pydantic models; max lengths; trimming; reject dangerous patterns
- CORS: strict origins only; no wildcards
- Rate limiting: Redis-based; per-IP and per-user for sensitive routes
- Headers: HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff, X-XSS-Protection; ensure present in responses
- Auditing: Log auth events (signup/login/refresh/logout) without sensitive data

### 9) Testing Requirements
- Unit tests (pytest, pytest-asyncio):
  - Auth: signup/login/refresh/logout; invalid/expired tokens; password policy; rate limiting
  - Security middleware: invalid JSON; malicious input; overly long payloads; query validation
  - CORS: preflight from allowed vs disallowed origins
  - Limiter with Redis (mock clock/time)
- Integration tests:
  - DB migrations apply; signing up persists user; logins and refreshes work across restarts
  - WS: server with Redis pub/sub; inject ticker pub; client receives `crypto_ticker_update`
  - Health endpoints: `/health`, `/readyz`, `/livez` reflect dependency state
- Performance (smoke):
  - Confirm p95 < 150ms for key REST endpoints under moderate load (document method)
- Coverage: ≥ 80% for modified backend modules; produce coverage artifact in CI

### 10) CI/CD & Deployment
- Update `.github/workflows/parallel-ci.yml`:
  - Start Postgres and Redis services in CI jobs for integration tests
  - Build backend Docker image; tag and push to GHCR (use `GHCR_PAT` secret)
  - On `main` with passing gates, deploy to Railway via CLI/API; retain existing quality-gate summary
  - Keep canary strategy for medium risk; block high risk
- `Dockerfile`:
  - Keep entrypoint: `python -m uvicorn backend.api.main_production:app --host 0.0.0.0 --port ${PORT:-8000}`
- `railway.json`:
  - Temporarily set workers to 1 until WS pub/sub verified; then 4 workers
- `docker-compose.yml`:
  - Add `postgres` and `redis`; ensure backend uses `backend.api.main_production:app`

---

## Data Models & Migrations
- `users` table:
  - `id UUID PK`, `email VARCHAR(254) UNIQUE NOT NULL`, `password_hash TEXT NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- Alembic revision: `0001_create_users` generated and applied

## Environment Variables (required unless noted)
- Core: `PYTHON_ENV`, `LOG_LEVEL`, `ALLOWED_ORIGINS`
- Auth: `JWT_SECRET_KEY`, `JWT_ISSUER`, `JWT_AUDIENCE`, `ACCESS_TOKEN_TTL_MIN=15`, `REFRESH_TOKEN_TTL_DAYS=7`
- Database: `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname`
- Redis: `REDIS_URL=redis://:password@host:6379/0`
- Observability: `SENTRY_DSN` (optional), `PROMETHEUS_ENABLED=true`
- Providers (optional): `CoinGecko_API_key`, `COINBASE_API_KEY`, `COINBASE_API_SECRET`, `newsapi_api_key`

## Error schema (all endpoints)
```json
{
  "error": {
    "code": "string",
    "message": "human readable",
    "details": { "field": "info" },
    "trace_id": "uuid"
  }
}
```
- Include `trace_id` in responses and logs; do not leak secrets or stack traces.

## Edge Cases to Handle
- Signup with existing email; weak password; invalid email format
- Login with wrong password; throttle brute force (rate limit)
- Expired/invalid access tokens; refresh reuse (old refresh must be invalidated)
- Redis unavailable: limiter conservatively degrades; WS falls back to local broadcast; log clearly
- DB unavailable: `/readyz` 503; dependent routes return 503 with trace id
- WS multi-worker: avoid duplicate sends; dedupe by message id if needed
- Provider outages: backoff and reuse last good snapshot with `stale=true`

## Acceptance Criteria
- All FE-required endpoints exist and return valid shapes (`frontend/src/services/api.js`)
- Auth persists users, enforces policies, supports token rotation + blacklist; all routes documented
- WS ticker broadcasts `crypto_ticker_update` within p95 < 250ms fetch-to-send; stable with 1 worker; plan to scale to 4 via Redis pub/sub
- `/metrics` exposes HTTP + custom metrics; `/readyz` fails when DB/Redis down; `/livez` OK when loop responsive
- CI passes: unit + integration tests; coverage ≥ 80%; security scans produce artifacts
- Container builds and deploys on Railway; app fails fast without required secrets; logs are structured JSON
- No placeholders; code is readable, typed, and matches existing style/formatting

## Files to Modify/Create (non-exhaustive)
- Modify:
  - `backend/api/main_production.py` (mount security; include `/api/v2/auth`; add `/readyz`, `/livez`; WS with Redis pub/sub)
  - `backend/middleware/security.py` (wire limiter to Redis; export limiter handler)
  - `backend/config/settings.py` (strict required env; parse CSV origins)
  - `frontend/src/services/api.js` (verify endpoint paths; no functional regression)
  - `.github/workflows/parallel-ci.yml` (services, build/push, deploy)
  - `docker-compose.yml` (add Postgres/Redis; run `main_production`)
  - `railway.json` (workers=1 until WS verified)
- Add:
  - `backend/db/{database.py,models.py,repositories.py,schemas.py}`
  - `backend/auth/{routes_v2.py,service.py,jwt.py,hashing.py}`
  - `backend/alembic/*` (migrations)
  - `backend/observability/{metrics.py,logging.py,sentry.py}`
  - `backend/ws/{pubsub.py,ticker_producer.py}`
  - Tests under `backend/tests/...` for auth, middleware, ws, health, endpoints
  - Docs updates and `.env.example`

## Style & Quality
- Strong typing; explicit function signatures; Pydantic models for requests/responses
- Early returns; shallow nesting; meaningful names; comments only where non-obvious
- Structured logging everywhere; avoid inline explanatory comments about actions
- Maintain existing indentation and formatting; do not reformat unrelated code

## What to Submit
- Code edits and new modules per above
- Test suite runnable via `pytest`
- Updated CI workflows & configs
- README changes including a “Production Readiness” runbook:
  - Local dev: `docker-compose up`
  - Tests: `pytest -q`
  - Health: `GET /health`, `/readyz`, `/livez`; Metrics: `GET /metrics`
  - Env var checklist

---

### Notes on Known Gaps to Fix
- CORS currently includes `"https://*.vercel.app"` which FastAPI does not support; replace with explicit origins from env.
- Default JWT secret exists in `backend/config/settings.py`; remove default and require env.
- `docker-compose.yml` points to a different app module for dev; align to `backend.api.main_production:app`.
- Frontend expects endpoints not currently implemented (`/api/bitcoin/sentiment`, `market-summary`, `news`, `analyze`, `/api/chat/history`, `/api/prompts`) and auth under `/api/v2/auth` — ensure parity.
- WS currently only echoes; implement real ticker producer and Redis pub/sub fanout.
