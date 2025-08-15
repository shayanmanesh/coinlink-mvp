# CoinLink MVP - Bitcoin Analysis Chat Application

A modern, responsive web application focused exclusively on Bitcoin (BTC) analysis with real-time trading charts, sentiment analysis, and proactive alerts.

## 🚀 Features

### Core Functionality
- **Bitcoin-Focused Chat Interface**: AI-powered analysis using TinyLlama-1.1B via Ollama
- **Real-Time Trading Charts**: TradingView widget locked to BTCUSD
- **Live Price Updates**: Coinbase Advanced API integration for BTC-USD data
- **Sentiment Analysis**: ProsusAI/finbert for Bitcoin news sentiment
- **Proactive Alerts**: Price changes, volume spikes, and sentiment shifts
- **Redis Caching**: 5-minute TTL for optimized performance

### User Interface
- **60% Chat Panel**: Bitcoin analysis interface with quick questions
- **40% TradingView Widget**: Interactive BTCUSD charts
- **Floating Alert Banner**: Real-time Bitcoin notifications
- **Sentiment Indicators**: Visual sentiment representation (🟢 bullish, 🔴 bearish, ⚪ neutral)
- **Mobile Responsive**: Stacked layout for mobile devices

### Sample Interactions
```
User: "What's happening with Bitcoin?"
Bot: "Bitcoin is trading at $45,230 (+3.2% 24h). RSI at 58 indicates neutral momentum. Recent news sentiment is bullish with 3 positive articles in the last hour."

User: "Should I buy?"
Bot: "Bitcoin's current setup shows moderate strength. Price above 50-day SMA ($44,100), neutral RSI, and positive sentiment. Consider your risk tolerance and investment timeline."

User: "Tell me about ETH"
Bot: "I focus exclusively on Bitcoin analysis. For BTC: current price $45,230 with stable volume. Would you like detailed Bitcoin metrics?"
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Web framework with WebSocket support
- **Langchain**: AI agent framework with TinyLlama integration
- **Ollama**: Local LLM serving for TinyLlama-1.1B
- **Redis**: Caching and session management
- **Transformers**: ProsusAI/finbert sentiment analysis

### Frontend
- **React**: Single-page application
- **Tailwind CSS**: Modern, responsive styling
- **WebSocket**: Real-time communication
- **TradingView Widget**: Interactive charts

### APIs & Services
- **Coinbase Advanced API**: Real-time BTC-USD data
- **NewsAPI**: Bitcoin news aggregation
- **Hugging Face**: Sentiment analysis models

## 📋 Prerequisites

- Docker and Docker Compose
- API keys for external services (see Environment Variables)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd coinlink-mvp
```

### 2. Set Environment Variables
Copy the example environment file and add your API keys:
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
OLLAMA_BASE_URL=http://localhost:11434
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_API_SECRET=your_coinbase_api_secret
REDIS_URL=redis://localhost:6379
HF_TOKEN=your_huggingface_token
CoinGecko_API_key=your_coingecko_api_key
Reddit_API_SECRET=your_reddit_api_secret
Reddit_client_id=your_reddit_client_id
newsapi_api_key=your_newsapi_api_key
messari_api_key=your_messari_api_key
```

### 3. Start the Application
```bash
docker-compose up -d
```

This will start:
- **Redis** (port 6379): Caching and session management
- **Ollama** (port 11434): TinyLlama model serving
- **Backend** (port 8000): FastAPI application
- **Frontend** (port 3000): React application

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Test Page**: http://localhost:8000/test

## 📁 Project Structure

```
coinlink-mvp/
├── backend/
│   ├── agents/
│   │   └── analyst.py          # Langchain agent with TinyLlama
│   ├── tools/
│   │   └── coinbase_tools.py   # Coinbase API integration
│   ├── sentiment/
│   │   └── analyzer.py         # finbert sentiment analysis
│   ├── monitors/
│   │   └── btc_monitor.py      # Async BTC monitoring
│   ├── alerts/
│   │   └── alert_engine.py     # Alert generation logic
│   ├── api/
│   │   ├── main.py             # FastAPI app
│   │   └── websocket.py        # WebSocket handlers
│   └── config/
│       └── settings.py         # Environment configuration
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main component
│   │   ├── components/
│   │   │   ├── Chat.jsx        # Bitcoin chat interface
│   │   │   ├── Chart.jsx       # TradingView widget
│   │   │   └── AlertBanner.jsx # Alert display
│   │   └── services/
│   │       └── api.js          # WebSocket connection
│   └── package.json
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔧 API Endpoints

### Chat & Analysis
- `POST /api/chat` - Send Bitcoin analysis request
- `GET /api/chat/history` - Get chat history

### Bitcoin Data
- `GET /api/bitcoin/price` - Current BTC price
- `GET /api/bitcoin/sentiment` - Sentiment analysis
- `GET /api/bitcoin/market-summary` - Comprehensive market data
- `GET /api/bitcoin/news` - Recent Bitcoin news

### Alerts & Monitoring
- `GET /api/alerts` - Active alerts
- `GET /api/alerts/history` - Alert history
- `GET /api/connections` - WebSocket connection count

### WebSocket
- `WS /ws` - Real-time updates and chat

## 🎯 Key Features Explained

### Bitcoin-Focused Analysis
The AI agent is specifically trained to focus exclusively on Bitcoin (BTC) analysis. It will redirect any queries about other cryptocurrencies back to Bitcoin analysis.

### Real-Time Monitoring
- **Price Monitoring**: Tracks BTC price changes with 5% threshold alerts
- **Volume Monitoring**: Detects volume spikes above 1M USD
- **Sentiment Monitoring**: Analyzes news sentiment changes
- **Background Processing**: Continuous monitoring every 30 seconds

### Sentiment Analysis
Uses ProsusAI/finbert model to analyze Bitcoin-related news articles, providing:
- Overall sentiment (positive/negative/neutral)
- Sentiment scores
- Article filtering for Bitcoin relevance
- Real-time sentiment updates

### Alert System
Proactive alerts for:
- **Price Alerts**: Significant BTC price movements
- **Volume Alerts**: Unusual trading volume
- **Sentiment Alerts**: Sentiment changes
- **Combined Alerts**: Price + sentiment correlation

## 🔍 Development

### Running Locally (without Docker)

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

### Testing
- **Backend**: http://localhost:8000/test (WebSocket test page)
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

## 🐛 Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   - Ensure Ollama is running: `docker-compose logs ollama`
   - Check if TinyLlama model is downloaded

2. **Redis Connection Error**
   - Verify Redis is running: `docker-compose logs redis`
   - Check Redis URL configuration

3. **API Key Errors**
   - Verify all API keys are set in `.env` file
   - Check API key permissions and quotas

4. **WebSocket Connection Issues**
   - Ensure backend is running on port 8000
   - Check CORS configuration

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs ollama
```

## 📈 Performance

- **Caching**: Redis with 5-minute TTL for Bitcoin data
- **Background Processing**: Async monitoring to prevent blocking
- **WebSocket**: Real-time updates without polling
- **Mobile Optimization**: Responsive design for all devices

## 🔒 Security

- **Environment Variables**: Secure API key management
- **CORS**: Configured for development (customize for production)
- **Input Validation**: All user inputs validated
- **Error Handling**: Comprehensive error handling and logging

## 🚀 Production Deployment

For production deployment:

1. **Environment Variables**: Use secure environment variable management
2. **SSL/TLS**: Configure HTTPS for WebSocket connections
3. **CORS**: Restrict origins to your domain
4. **Monitoring**: Add application monitoring and logging
5. **Scaling**: Consider horizontal scaling for high traffic

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**CoinLink MVP** - Your Bitcoin Analysis Companion 🚀
