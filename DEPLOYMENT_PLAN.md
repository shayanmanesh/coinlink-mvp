# CoinLink Production Deployment Plan
## Target: www.coin.link

### Executive Summary
This plan outlines the steps to deploy CoinLink from local development to production at www.coin.link. Estimated timeline: 2-3 weeks with proper resources.

---

## 🚀 Phase 1: Infrastructure Setup (Days 1-2)

### Cloud Provider Selection (Recommended: AWS)
```bash
# Core Services Needed:
- EC2/ECS for application hosting
- RDS PostgreSQL for persistent data
- ElastiCache Redis for caching
- S3 for static assets
- CloudFront CDN
- Route53 for DNS
- ALB for load balancing
- ECS Fargate for container orchestration
```

### Alternative: Vercel + Railway/Render
```bash
# Simpler Setup:
- Vercel for frontend (automatic SSL, CDN, scaling)
- Railway/Render for backend API
- Upstash Redis for caching
- Supabase PostgreSQL for database
- Cloudflare for DNS
```

### Infrastructure as Code
```yaml
# terraform/main.tf structure:
- VPC with public/private subnets
- Security groups for services
- ECS cluster configuration
- RDS instance
- Redis cluster
- S3 buckets
- CloudFront distribution
```

---

## 🔐 Phase 2: Security & Configuration (Days 3-4)

### Secrets Management
```bash
# AWS Secrets Manager setup:
aws secretsmanager create-secret --name coinlink/production/api-keys
aws secretsmanager create-secret --name coinlink/production/jwt-secret
aws secretsmanager create-secret --name coinlink/production/database-url
```

### Environment Configuration
```env
# Production .env.production:
NODE_ENV=production
REACT_APP_API_URL=https://api.coin.link
REACT_APP_WS_URL=wss://api.coin.link/ws

# Backend configuration:
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET=${AWS_SECRET}
COINBASE_API_KEY=${AWS_SECRET}
```

### SSL/TLS Setup
```bash
# AWS Certificate Manager:
aws acm request-certificate --domain-name coin.link --subject-alternative-names "*.coin.link"

# Or use Certbot for Let's Encrypt:
certbot certonly --webroot -w /var/www/html -d coin.link -d www.coin.link
```

---

## 💾 Phase 3: Database & Persistence (Days 5-6)

### PostgreSQL Schema
```sql
-- migrations/001_initial.sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    subscription_tier VARCHAR(50) DEFAULT 'free'
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    message TEXT NOT NULL,
    response TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE rate_limits (
    user_id UUID REFERENCES users(id),
    prompts_used INTEGER DEFAULT 0,
    reset_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id)
);
```

### Redis Configuration
```yaml
# redis.conf for production:
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
appendonly yes
```

---

## ⚡ Phase 4: Application Optimization (Days 7-8)

### Frontend Optimization
```javascript
// package.json additions:
{
  "scripts": {
    "build:prod": "GENERATE_SOURCEMAP=false react-scripts build",
    "analyze": "source-map-explorer 'build/static/js/*.js'"
  }
}

// Implement code splitting:
const TradingViewWidget = lazy(() => import('./components/TradingViewWidget'));
const Chat = lazy(() => import('./components/Chat'));
```

### Backend Optimization
```python
# backend/config/production.py
from pydantic import BaseSettings

class ProductionSettings(BaseSettings):
    # Connection pooling
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis connection pool
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    
    # CORS production domains
    ALLOWED_ORIGINS: list = [
        "https://coin.link",
        "https://www.coin.link"
    ]
```

### Docker Optimization
```dockerfile
# Multi-stage build for frontend
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build:prod

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
```

---

## 🔄 Phase 5: CI/CD Pipeline (Days 9-10)

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          npm test
          python -m pytest backend/tests

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker images
        run: |
          docker build -t coinlink-frontend ./frontend
          docker build -t coinlink-backend ./backend
          
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          
          docker tag coinlink-frontend:latest $ECR_REGISTRY/coinlink-frontend:latest
          docker tag coinlink-backend:latest $ECR_REGISTRY/coinlink-backend:latest
          
          docker push $ECR_REGISTRY/coinlink-frontend:latest
          docker push $ECR_REGISTRY/coinlink-backend:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster coinlink-cluster --service coinlink-frontend --force-new-deployment
          aws ecs update-service --cluster coinlink-cluster --service coinlink-backend --force-new-deployment
```

---

## 📊 Phase 6: Monitoring & Scaling (Days 11-12)

### CloudWatch Configuration
```yaml
# cloudwatch-alarms.yml
Alarms:
  - HighCPU:
      MetricName: CPUUtilization
      Threshold: 80
      ComparisonOperator: GreaterThanThreshold
      
  - HighMemory:
      MetricName: MemoryUtilization
      Threshold: 85
      ComparisonOperator: GreaterThanThreshold
      
  - APIErrors:
      MetricName: 5XXError
      Threshold: 10
      Period: 300
```

### Auto-Scaling Configuration
```json
{
  "targetCapacity": 2,
  "minCapacity": 1,
  "maxCapacity": 10,
  "targetTrackingScalingPolicies": [{
    "metricType": "ECSServiceAverageCPUUtilization",
    "targetValue": 70
  }]
}
```

### Application Monitoring
```python
# backend/monitoring.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc import trace_exporter
from opentelemetry.sdk.trace import TracerProvider

# Setup OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add to main.py
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)
```

---

## 🌐 Phase 7: Domain & DNS Configuration (Day 13)

### Domain Setup
```bash
# Route53 or Cloudflare DNS records:
A     www.coin.link    -> CloudFront Distribution
A     coin.link        -> CloudFront Distribution
CNAME api.coin.link    -> ALB DNS name
MX    coin.link        -> Email provider
TXT   _dmarc.coin.link -> DMARC policy
```

### CDN Configuration
```json
{
  "CloudFrontDistribution": {
    "Origins": [{
      "DomainName": "alb-123456.us-east-1.elb.amazonaws.com",
      "OriginPath": "",
      "CustomOriginConfig": {
        "OriginProtocolPolicy": "https-only"
      }
    }],
    "DefaultCacheBehavior": {
      "TargetOriginId": "ALB-Origin",
      "ViewerProtocolPolicy": "redirect-to-https",
      "CachePolicyId": "optimized-caching"
    }
  }
}
```

---

## ✅ Phase 8: Testing & Launch (Days 14-15)

### Pre-Launch Checklist
```markdown
- [ ] SSL certificates verified
- [ ] Database migrations completed
- [ ] Redis cache warming
- [ ] Load testing completed (use K6 or Artillery)
- [ ] Security scan passed (OWASP ZAP)
- [ ] Backup strategy implemented
- [ ] Rollback procedure documented
- [ ] Error tracking setup (Sentry)
- [ ] Analytics configured (Google Analytics)
- [ ] Legal pages added (Privacy, Terms)
```

### Load Testing Script
```javascript
// k6-load-test.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 100 },
    { duration: '10m', target: 100 },
    { duration: '5m', target: 0 },
  ],
};

export default function() {
  let response = http.get('https://api.coin.link/health');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
}
```

### Deployment Commands
```bash
# Final deployment sequence:
./scripts/run-tests.sh
./scripts/database-backup.sh
./scripts/deploy-production.sh
./scripts/smoke-tests.sh
./scripts/enable-traffic.sh
```

---

## 📈 Post-Launch Monitoring

### Key Metrics to Track
- Response time (P50, P95, P99)
- Error rates (4XX, 5XX)
- WebSocket connection stability
- Database query performance
- Redis cache hit ratio
- User engagement metrics
- Cost per user

### Gradual Rollout Strategy
```yaml
Week 1: 10% traffic (beta users)
Week 2: 25% traffic
Week 3: 50% traffic
Week 4: 100% traffic
```

---

## 💰 Estimated Costs (AWS)

| Service | Monthly Cost |
|---------|-------------|
| ECS Fargate (2 tasks) | $50 |
| RDS PostgreSQL (t3.small) | $30 |
| ElastiCache Redis | $25 |
| CloudFront CDN | $20 |
| Route53 | $1 |
| S3 Storage | $5 |
| Data Transfer | $30 |
| **Total** | **~$161/month** |

---

## 🚨 Critical Success Factors

1. **API Keys**: Ensure all third-party API keys are obtained and tested
2. **WebSocket Scaling**: Implement sticky sessions for WebSocket connections
3. **Rate Limiting**: Enforce rate limits at multiple levels (CloudFront, API Gateway, Application)
4. **Data Compliance**: Implement GDPR/CCPA compliance if serving EU/CA users
5. **Backup Strategy**: Daily automated backups with 30-day retention

---

## Next Immediate Steps

1. **Choose hosting strategy** (AWS full-stack vs Vercel+Railway)
2. **Purchase/verify domain** ownership for coin.link
3. **Set up development/staging environments** first
4. **Obtain production API keys** from all providers
5. **Create CI/CD pipeline** for automated deployments

This plan provides a production-ready, scalable architecture for CoinLink that can handle significant traffic while maintaining security and performance standards.