# CoinLink API Keys Documentation
## Production Environment Setup Guide

Last Updated: 2025-08-16

---

## 🔑 Required API Keys for Production

### 1. **Coinbase Advanced Trade API** ⭐ CRITICAL
- **Purpose**: Real-time cryptocurrency price data, trading signals, and market depth
- **Required Variables**:
  - `COINBASE_API_KEY`: Your Coinbase API key
  - `COINBASE_API_SECRET`: Your Coinbase API secret
  - `COINBASE_KEY_JSON`: JWT authentication key (for CDP API)
- **How to Obtain**:
  1. Go to https://www.coinbase.com/settings/api
  2. Create a new API key with "View" permissions
  3. For Advanced Trade API, visit https://portal.cdp.coinbase.com/
  4. Create a project and generate API credentials
- **Security Level**: HIGH - Never commit to repository
- **Cost**: Free tier available, paid tiers for higher limits

### 2. **Redis Database** ⭐ CRITICAL
- **Purpose**: Caching, session management, real-time data storage
- **Required Variables**:
  - `REDIS_URL`: Full Redis connection URL
  - `REDIS_TLS_URL`: Secure Redis connection (for production)
- **How to Obtain**:
  1. Railway: Provision Redis from Railway dashboard
  2. Alternative: Use Redis Cloud (https://redis.com/redis-enterprise-cloud/)
  3. Get connection string from provider dashboard
- **Security Level**: HIGH - Contains database credentials
- **Cost**: Railway ~$5/month, Redis Cloud free tier available

### 3. **Hugging Face Token** ⭐ IMPORTANT
- **Purpose**: Sentiment analysis using FinBERT model
- **Required Variables**:
  - `HF_TOKEN`: Your Hugging Face API token
- **How to Obtain**:
  1. Sign up at https://huggingface.co/
  2. Go to Settings → Access Tokens
  3. Create new token with "read" access
- **Security Level**: MEDIUM
- **Cost**: Free tier sufficient for MVP

### 4. **CoinGecko API** 📊 RECOMMENDED
- **Purpose**: Historical price data, market cap, volume analytics
- **Required Variables**:
  - `CoinGecko_API_key`: Your CoinGecko API key
- **How to Obtain**:
  1. Sign up at https://www.coingecko.com/en/api
  2. Choose plan (Demo API is free)
  3. Get API key from dashboard
- **Security Level**: LOW
- **Cost**: Free demo API (10-50 calls/min), Pro starts at $129/month

### 5. **Reddit API** 📱 OPTIONAL
- **Purpose**: Social sentiment monitoring from crypto subreddits
- **Required Variables**:
  - `Reddit_API_SECRET`: Reddit app secret
  - `Reddit_client_id`: Reddit app client ID
- **How to Obtain**:
  1. Go to https://www.reddit.com/prefs/apps
  2. Create a new app (select "script" type)
  3. Note the client ID and secret
- **Security Level**: MEDIUM
- **Cost**: Free

### 6. **News API** 📰 OPTIONAL
- **Purpose**: Cryptocurrency news aggregation
- **Required Variables**:
  - `newsapi_api_key`: Your NewsAPI key
- **How to Obtain**:
  1. Sign up at https://newsapi.org/
  2. Get API key from account page
- **Security Level**: LOW
- **Cost**: Free tier (100 requests/day), paid plans from $449/month

### 7. **Messari API** 📈 OPTIONAL
- **Purpose**: Professional crypto research and on-chain metrics
- **Required Variables**:
  - `messari_api_key`: Your Messari API key
- **How to Obtain**:
  1. Sign up at https://messari.io/api
  2. Request API access
  3. Get key from dashboard
- **Security Level**: MEDIUM
- **Cost**: Free tier limited, Pro pricing on request

### 8. **Sentry (Error Tracking)** 🐛 HIGHLY RECOMMENDED
- **Purpose**: Production error tracking and performance monitoring
- **Required Variables**:
  - `SENTRY_DSN`: Your Sentry project DSN
- **How to Obtain**:
  1. Sign up at https://sentry.io/
  2. Create new project (select Python)
  3. Copy DSN from project settings
- **Security Level**: LOW (DSN is meant to be public)
- **Cost**: Free tier (5K errors/month), Team plan $26/month

### 9. **JWT & Session Secrets** 🔐 CRITICAL
- **Purpose**: Authentication and session security
- **Required Variables**:
  - `JWT_SECRET`: Strong random string for JWT signing
  - `SESSION_SECRET`: Strong random string for session encryption
- **How to Generate**:
  ```bash
  # Generate secure random strings
  openssl rand -hex 32  # For JWT_SECRET
  openssl rand -hex 32  # For SESSION_SECRET
  ```
- **Security Level**: CRITICAL - Never share or commit
- **Cost**: Free (self-generated)

---

## 📋 Priority Levels

### 🔴 **CRITICAL** (Must have for launch)
1. Coinbase API credentials
2. Redis connection
3. JWT/Session secrets

### 🟡 **IMPORTANT** (Highly recommended)
1. Hugging Face token (for sentiment analysis)
2. Sentry DSN (for error tracking)

### 🟢 **NICE TO HAVE** (Can add later)
1. CoinGecko API
2. Reddit API
3. News API
4. Messari API
5. Notification webhooks (Discord/Slack/Telegram)

---

## 🚀 Quick Setup Script

```bash
# Copy this to set up your environment variables in Railway

# Critical
COINBASE_API_KEY="your-coinbase-api-key"
COINBASE_API_SECRET="your-coinbase-api-secret"
REDIS_URL="redis://default:password@redis.railway.internal:6379"
JWT_SECRET="$(openssl rand -hex 32)"
SESSION_SECRET="$(openssl rand -hex 32)"

# Important
HF_TOKEN="your-huggingface-token"
SENTRY_DSN="your-sentry-dsn"

# Optional (can leave empty initially)
CoinGecko_API_key=""
Reddit_API_SECRET=""
Reddit_client_id=""
newsapi_api_key=""
messari_api_key=""
```

---

## 🔒 Security Best Practices

1. **Never commit API keys** to the repository
2. **Use environment variables** exclusively
3. **Rotate keys regularly** (every 90 days minimum)
4. **Use different keys** for development/staging/production
5. **Monitor API usage** to detect anomalies
6. **Set up IP restrictions** where possible
7. **Use read-only permissions** when write access isn't needed
8. **Enable 2FA** on all service accounts

---

## 📊 Estimated Monthly Costs

### Minimum Viable Product (MVP)
- Railway hosting: ~$5-20/month
- Redis: $5/month (Railway) or free tier
- **Total: ~$10-25/month**

### Growth Phase
- Railway hosting: $20-50/month
- Redis: $10-20/month
- CoinGecko Pro: $129/month
- Sentry Team: $26/month
- **Total: ~$185-225/month**

### Scale Phase
- Infrastructure: $200-500/month
- Premium APIs: $500-1000/month
- Monitoring/Analytics: $100-200/month
- **Total: ~$800-1700/month**

---

## 🆘 Troubleshooting

### Common Issues:

1. **"Invalid API Key" errors**
   - Check for trailing spaces in environment variables
   - Ensure keys are properly escaped in .env file
   - Verify key permissions match required scope

2. **Redis connection failures**
   - Check if Redis URL includes protocol (redis:// or rediss://)
   - Verify firewall/security group settings
   - Test connection with redis-cli

3. **Rate limiting issues**
   - Implement exponential backoff
   - Cache API responses aggressively
   - Consider upgrading to paid tiers

4. **CORS errors**
   - Ensure frontend domain is in CORS_ORIGINS
   - Check for protocol mismatches (http vs https)

---

## 📞 Support Contacts

- **Coinbase Support**: https://help.coinbase.com/
- **Railway Support**: https://railway.app/help
- **Redis Support**: https://redis.com/company/support/
- **Sentry Support**: https://sentry.io/support/

---

## ✅ Pre-Deployment Checklist

- [ ] All CRITICAL API keys obtained and tested
- [ ] Redis connection verified
- [ ] JWT/Session secrets generated (32+ characters)
- [ ] Sentry project created and DSN configured
- [ ] Environment variables set in Railway dashboard
- [ ] API rate limits understood and documented
- [ ] Backup API keys stored securely
- [ ] Team members have access to shared credentials vault
- [ ] Monitoring alerts configured
- [ ] Cost tracking enabled for all services