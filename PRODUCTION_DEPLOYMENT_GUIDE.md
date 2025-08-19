# CoinLink Production Deployment Guide

## 🚀 Production Hardening Complete

This guide documents the complete production-ready deployment of CoinLink MVP with comprehensive security, scalability, and observability features.

## 📋 Production Readiness Checklist

### ✅ Phase 1: Dependencies & Environment
- [x] Updated to Python 3.11 with pinned production dependencies
- [x] Added SQLAlchemy 2.0 with async PostgreSQL support
- [x] Integrated Redis for caching and WebSocket pub/sub
- [x] Added comprehensive security packages (passlib, JWT, rate limiting)

### ✅ Phase 2: Security & Middleware
- [x] Pydantic settings with strict validation (no default secrets)
- [x] Redis-backed rate limiting with graceful degradation
- [x] CORS middleware with environment-specific origins
- [x] Security headers and request/response logging

### ✅ Phase 3: Database & Authentication
- [x] PostgreSQL models with proper indexing and relationships
- [x] JWT authentication with access/refresh token rotation
- [x] BCrypt password hashing with configurable rounds
- [x] Session management with blacklisting capabilities

### ✅ Phase 4: WebSocket & Real-time Features
- [x] Redis pub/sub WebSocket manager for horizontal scaling
- [x] Real-time market data and notification services
- [x] Connection tracking and message broadcasting

### ✅ Phase 5: API Endpoints & Frontend Parity
- [x] Complete API v2 routes with proper validation
- [x] Market data endpoints with caching
- [x] User management with profile and preferences
- [x] Notification system with real-time updates

### ✅ Phase 6: Observability & Monitoring
- [x] Prometheus metrics with SLA tracking
- [x] Structured JSON logging with trace correlation
- [x] Sentry integration for error tracking
- [x] Custom business logic metrics

### ✅ Phase 7: Comprehensive Testing
- [x] Unit tests with ≥80% coverage
- [x] Integration tests for all major components
- [x] WebSocket and auth testing
- [x] Observability and metrics testing

### ✅ Phase 8: Docker & CI/CD
- [x] Multi-stage production Dockerfile with security hardening
- [x] Docker Compose with PostgreSQL, Redis, health checks
- [x] GitHub Actions CI/CD with security scanning
- [x] Railway deployment with staging/production gates

### ✅ Phase 9: Documentation & Verification
- [x] Production deployment documentation
- [x] Environment configuration guides
- [x] Monitoring and alerting setup
- [x] Disaster recovery procedures

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Load Balancer  │    │   CDN/Static    │
│   React/Vercel  │◄──►│   Railway/Render │◄──►│   Assets        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend Services                         │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   FastAPI API   │   WebSocket     │   Background    │  Metrics  │
│   REST/GraphQL  │   Real-time     │   Tasks/Jobs    │  /Health  │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   PostgreSQL    │ │     Redis       │ │   External      │
    │   Primary DB    │ │  Cache/Pub/Sub  │ │   APIs/Services │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 🔧 Environment Setup

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Python 3.11+
- GitHub account for CI/CD
- Railway/Render account for deployment

### Environment Variables

Copy `.env.production.example` to `.env.production` and configure:

```bash
# Required Security Settings
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
REDIS_URL=redis://host:port/0
JWT_SECRET_KEY=your_ultra_secure_jwt_secret_key_minimum_32_characters
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# External Services
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
COINBASE_API_KEY=your_coinbase_api_key
COINGECKO_API_KEY=your_coingecko_api_key
```

## 🚀 Deployment Methods

### Method 1: Railway (Recommended)
```bash
# 1. Connect GitHub repository to Railway
# 2. Set environment variables in Railway dashboard
# 3. Deploy automatically on git push to main

git push origin main
```

### Method 2: Docker Compose (Local/VPS)
```bash
# 1. Clone repository
git clone https://github.com/your-org/coinlink-mvp
cd coinlink-mvp

# 2. Configure environment
cp .env.production.example .env.production
# Edit .env.production with your values

# 3. Deploy with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# 4. Check health
curl http://localhost:8000/health
```

### Method 3: Manual Deployment
```bash
# 1. Install dependencies
pip install -r backend/requirements-production.txt

# 2. Set environment variables
export DATABASE_URL="your_database_url"
export JWT_SECRET_KEY="your_secret_key"

# 3. Run database migrations
alembic upgrade head

# 4. Start application
uvicorn backend.api.main_production:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📊 Monitoring & Observability

### Health Checks
- **Health Endpoint**: `GET /health`
- **Readiness Check**: `GET /readyz` 
- **Metrics**: `GET /metrics` (Prometheus format)

### Key Metrics to Monitor
- **API Response Time**: p95 < 150ms (SLA target)
- **WebSocket Latency**: p95 < 250ms (SLA target)
- **Error Rate**: < 1% (SLA target)
- **Database Connections**: Monitor pool usage
- **Redis Memory**: Monitor cache hit rate

### Logging
Structured JSON logs with trace correlation:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO", 
  "message": "API request completed",
  "trace_id": "abc123",
  "user_id": "user_456",
  "endpoint": "/api/v1/bitcoin/price",
  "duration_ms": 45,
  "status_code": 200
}
```

### Alerting Setup

#### Critical Alerts (Immediate Response)
- API error rate > 5%
- Database connection failures
- Redis unavailable
- Memory usage > 90%

#### Warning Alerts (Monitor)
- API response time p95 > 200ms
- WebSocket connection drops
- High memory usage (> 80%)
- External API failures

## 🔐 Security Features

### Authentication & Authorization
- JWT tokens with rotation every 24 hours
- Refresh tokens with 7-day expiry
- Token blacklisting on logout
- Rate limiting per user and IP

### Data Protection
- BCrypt password hashing (14 rounds in production)
- SQL injection prevention via SQLAlchemy ORM
- CORS protection with environment-specific origins
- Request/response logging (excluding sensitive data)

### Infrastructure Security
- Non-root Docker containers
- Multi-stage builds minimizing attack surface
- Security scanning in CI/CD pipeline
- Secrets management via environment variables

## 📈 Performance Optimizations

### Database
- Connection pooling (10-20 connections)
- Query optimization with proper indexing
- Async SQLAlchemy for high concurrency

### Caching
- Redis caching for market data (5-minute TTL)
- Session storage in Redis
- Rate limiting counters in Redis

### WebSocket
- Redis pub/sub for horizontal scaling
- Connection tracking and cleanup
- Message batching for efficiency

## 🔄 CI/CD Pipeline

### Automated Testing
- Security scanning with Trivy
- Unit tests with pytest (≥80% coverage)
- Integration tests with test database
- Docker image vulnerability scanning

### Deployment Gates
- Staging deployment with health checks
- Production gates requiring staging success
- Automated rollback on failure
- Smoke tests post-deployment

### Branch Strategy
- `main` branch deploys to production
- `feat/*` branches deploy to staging
- Pull requests require CI passing

## 🆘 Disaster Recovery

### Database Backup
```bash
# Automated daily backups
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Point-in-time recovery available (Railway/managed services)
```

### Application Recovery
```bash
# Rollback to previous deployment
railway rollback --service coinlink-backend

# Or deploy specific commit
git checkout abc123
git push origin main --force
```

### Monitoring Recovery
1. Check health endpoints
2. Verify key metrics in Prometheus
3. Test critical user flows
4. Monitor error rates for 30 minutes

## 📝 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database status
pg_isready -h your_host -p 5432

# Verify connection string
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"
```

#### Redis Connection Issues
```bash
# Check Redis status  
redis-cli -h your_host -p 6379 ping

# Test connection
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

#### High Memory Usage
```bash
# Check container stats
docker stats coinlink-backend

# Monitor specific endpoints
curl http://localhost:8000/metrics | grep memory
```

### Performance Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Monitor slow queries
# Check Sentry for performance insights
# Use /metrics endpoint for detailed metrics
```

## 🎯 Production SLA Targets

### Response Time
- REST API p95: < 150ms
- WebSocket messages p95: < 250ms
- Health checks: < 50ms

### Availability
- Uptime: 99.9% (8.76 hours downtime/year)
- Error rate: < 1%
- Recovery time: < 5 minutes

### Scalability
- Support 1000+ concurrent users
- Handle 10,000+ requests/minute
- WebSocket connections: 5,000+

## 📚 Additional Resources

- [API Documentation](./API_DOCS.md)
- [Database Schema](./backend/db/models.py)
- [WebSocket Events](./backend/websocket/events.py)
- [Metrics Guide](./backend/observability/metrics.py)
- [Testing Guide](./backend/tests/README.md)

---

**🎉 Production Hardening Complete!**

The CoinLink MVP is now production-ready with enterprise-grade security, monitoring, and scalability features. All 9 phases of production hardening have been successfully implemented and verified.