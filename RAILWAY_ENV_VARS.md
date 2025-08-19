# Railway Environment Variables Configuration

## Production Environment Variables for www.coin.link

### Required Environment Variables

These environment variables MUST be configured in Railway dashboard before deployment:

#### Core Configuration
```bash
# Port (automatically set by Railway)
PORT=8000  # Railway will override this

# Environment
NODE_ENV=production
PYTHON_ENV=production
```

#### Supabase Configuration
```bash
# Required for database and authentication
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key  # Only if admin operations needed
```

#### CORS Configuration
```bash
# Frontend URLs for CORS
FRONTEND_URL=https://www.coin.link
ALLOWED_ORIGINS=https://www.coin.link,https://coin.link,https://frontend-oyhz3vvwf-shayans-projects-ede8d66b.vercel.app
```

#### API Keys (Add as needed)
```bash
# Crypto Data Providers (choose one or more)
COINGECKO_API_KEY=your_coingecko_api_key
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
COINMARKETCAP_API_KEY=your_coinmarketcap_api_key

# News and Sentiment
NEWS_API_KEY=your_news_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# AI/ML Services (if implementing full features)
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
HUGGINGFACE_TOKEN=your_huggingface_token
```

#### Security & Monitoring
```bash
# JWT Configuration
JWT_SECRET_KEY=generate_a_secure_random_string_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring (optional)
SENTRY_DSN=your_sentry_dsn_if_using_sentry
LOG_LEVEL=info  # debug, info, warning, error
```

#### Redis Configuration (if using caching)
```bash
REDIS_URL=redis://default:password@host:port
REDIS_ENABLE_CACHE=true
REDIS_TTL=3600
```

### Optional Environment Variables

These can be added later as features are implemented:

```bash
# WebSocket Configuration
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=1000

# Feature Flags
ENABLE_LIVE_TRADING=false
ENABLE_AI_AGENTS=false
ENABLE_PREMIUM_FEATURES=false

# External Services
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DISCORD_WEBHOOK_URL=your_discord_webhook_url
SLACK_WEBHOOK_URL=your_slack_webhook_url

# Database Connection Pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Crypto Network RPCs (for on-chain data)
ETHEREUM_RPC_URL=your_ethereum_rpc_url
BSC_RPC_URL=your_bsc_rpc_url
POLYGON_RPC_URL=your_polygon_rpc_url
```

## How to Configure in Railway

1. **Via Railway Dashboard:**
   - Go to your project in Railway dashboard
   - Select your service
   - Click on "Variables" tab
   - Add each variable with its value
   - Railway will automatically restart the service

2. **Via Railway CLI:**
   ```bash
   # Set individual variables
   railway variables set SUPABASE_URL=your_url
   railway variables set SUPABASE_ANON_KEY=your_key
   
   # Or use a .env file
   railway variables set --from-file .env.production
   ```

3. **Via railway.json (NOT recommended for secrets):**
   - Only use for non-sensitive configuration
   - Secrets should always be set via dashboard or CLI

## Environment-Specific Configuration

### Production Environment
- Use the variables listed above
- Ensure all API keys are production keys
- Set LOG_LEVEL to "info" or "warning"
- Enable rate limiting
- Use production database

### Staging Environment
- Use separate API keys for testing
- Set LOG_LEVEL to "debug"
- Use staging database
- Lower rate limits for testing

## Security Best Practices

1. **Never commit secrets to Git**
2. **Use Railway's variable groups** for shared configuration
3. **Rotate keys regularly**
4. **Use different keys for different environments**
5. **Enable Railway's secret scanning**

## Verification

After setting environment variables:

1. Check deployment logs:
   ```bash
   railway logs --tail
   ```

2. Verify health endpoint:
   ```bash
   curl https://your-app.railway.app/health
   ```

3. Test API endpoints:
   ```bash
   curl https://your-app.railway.app/api/bitcoin/price
   ```

## Common Issues

### Issue: CORS errors
- Ensure ALLOWED_ORIGINS includes your frontend URL
- Check that credentials are included in requests

### Issue: Database connection failed
- Verify SUPABASE_URL and keys are correct
- Check network connectivity from Railway

### Issue: WebSocket disconnections
- Increase WS_HEARTBEAT_INTERVAL
- Check Railway's WebSocket timeout settings

### Issue: High memory usage
- Reduce worker count in production
- Enable memory monitoring in Railway

## Support

For Railway-specific issues:
- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app

For CoinLink issues:
- Check deployment logs: `railway logs`
- Monitor health endpoint: `/health`
- Review error responses in API