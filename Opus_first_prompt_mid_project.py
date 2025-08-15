```
I'm working on CoinLink MVP - Bitcoin chat app with:
- TinyLlama via Ollama for chat
- WebSocket real-time prices
- Chat-based registration (/register command)
- ProsusAI/finbert sentiment
- Rate limiting with slowapi

The CoinLink app has a single-page layout with two independent interfaces:

**Left (default: 60%)**: Chat interface featuring a Specialized Agent
- Message history display
- Input box with "/register" prompt
- System messages for registration flow
- Bitcoin analysis responses through specialized multi-modal user-facing and proactive Agent
- Real-time agent alerts (RSI, volume spikes)

**Right (default: 40%)**: TradingView chart widget
- Live BTCUSD candlestick chart
- Embedded iframe from TradingView
- Independent zoom/pan controls
- No data exchange with chat

**Layout structure of Chart Interface (top to bottom):**

1. **Continuous tick-by-tick real-time Ticker Feed** (top bar):
   - Shows real-time Top 50 Crypto prices ranked by market cap.
   - Continuous horizontal moving-feed ticker
   - Single line with time-based price and percentage changes: SOL $145.00 (+5.67%)  • XRP $2.21 (-2.12%) 
   

2. **Bitcoin Feed** (below ticker feed):
   - Format: `Bitcoin (BTC) $118,540.25   1h +4.47% • 24h -2.92% • 7d -11.07% • 30d -15.97%`
   - Single line
   

Bitcoin & Ticker feeds, ensure equal height and unified color (background, price, etc)

Price colors:

Up/Positive: 
#00D964 (bright green)
Down/Negative: 
#FF3737 (bright red)
Unchanged: 
#A0A0A0 (neutral gray)
Text elements:

Symbol: 
#FFFFFF (white)
Percentage: Same as price direction
flash on update:

Green flash: #00D96420 (20% opacity)
Red flash: #FF373720 (20% opacity)
These follow Bloomberg/trading terminal conventions for maximum readability and quick visual scanning.
No bold for ticker prices.
Regular weight for prices
Color for direction (green/red)
Size hierarchy if needed (larger for price, smaller for percentage)
Exception: Bold the ticker symbol only (e.g., BTC $118,777.67)
Symbol: Use "Bitcoin (BTC)" - provides both name and ticker for clarity.

For ticker live feed on dark background:
Price colors:

Up/Positive: #00D964 (bright green)
Down/Negative: #FF3737 (bright red)
Unchanged: #A0A0A0 (neutral gray)

Text elements:

Symbol: #FFFFFF (white)
Percentage: Same as price direction
Volume: #8B92A8 (muted blue-gray)

Background flash on update:

Green flash: #00D96420 (20% opacity)
Red flash: #FF373720 (20% opacity)

These follow Bloomberg/trading terminal conventions for maximum readability and quick visual scanning.


Other optimizations:

Add thousand separators: $118,105.84
Align decimal points vertically across time periods
Consider adding subtle dividers between time periods
Right-align all percentage values for easier scanning
The green percentages are well-chosen for positive movement.

Analyzed optimal ticker formatting for enhanced readability and clarity.

BNB $567.89 (+3.12%)  •  SOL $145.67 (+5.67%)
Better because:

Space after symbol improves readability
Parentheses clarify percentage is supplementary
Bullet separator (•) creates visual boundaries
No bold needed - let color coding do the work

Flash only the price value, not the entire bar.
Current subtle flash is good - confirms update received.

Best practice:

Price number flashes green/red (200ms duration)
Background stays constant
Keeps focus on the changing data
This mirrors professional trading terminals.


3. **Main Content** (split view):
   - Left 60%: Chat interface
   - Right 40%: TradingView chart
   - split view sizing adjustable with vertical divider for user customization based on user preference.

**Bitcoin feed population:**
- WebSocket connection to backend (`ws://localhost:8000/ws`)
- Backend has two data sources:
  1. Coinbase WebSocket (production)
  2. REST API poller (fallback, polls every 1s)
- Updates flow: Coinbase → Backend → WebSocket → Frontend
- RSI, support/resistance calculated server-side
- Frontend receives `price_update` messages with price, timestamp, RSI, volume
- ensure connection to coinbase api 

The Bitcoin feed should auto-update every 1-2 seconds as new price data arrives via WebSocket.
Coinbase Advanced Trade WebSocket APIs can be accessed:
# Load .env
load_dotenv()

# Parse key JSON
key_json = json.loads(os.getenv("COINBASE_KEY_JSON"))
API_KEY_NAME = key_json["name"]
PRIVATE_KEY = key_json["privateKey"]

The interfaces don't communicate - chart movements don't trigger chat updates, and chat queries don't affect chart display. They're visually unified but functionally separate components sharing the same page.
Note enhancement opportunity: implement Technical Analyst Agent dedicated to absorbing Coinbase data, and generating real-time technical analysis and market data update pushed to Senior Analyst (Specialized Agent coordinating with user) and providing a technical bitcoin report summary pushed into the Chat UI Prompt Feed every 30 minutes. When user clicks on preloaded prompt, Senior Analyst outputs the report in chat.

Current issue, Chart Interface:
Current alignment issue: 
- Bitcoin feed bleeds, chart has uneven margins (more space left, less right), data cut-off: 30d percentage cut off. Need uniform 16px margins. Margins should be precisely aligned between Ticker Feed, Bitcoin Feed, Chart. Contain datapoints within their respective containers.
- Ensure webpage is smart and responsive to different display sizes.
- Ticker feed needs to reflect top 50 crypto tickers ranked by marketcap (don't include USDT which is fixed at $1.00)

Bitcoin feed text overlaps chat interface
Chart not centered (left margin > right margin)
30d percentage truncated
Need consistent padding/margins across all containers

```
FIX LAYOUT ALIGNMENT ISSUES:

1. TICKER CONTAINER:
```css
.ticker-container {
  position: relative;
  width: 100%;
  height: 40px;
  background: #0a0a0a;
  border-bottom: 1px solid #2d3748;
  overflow: hidden;
  z-index: 10; /* Prevent bleeding into chat */
}

.bitcoin-ticker {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 16px;
  gap: 12px;
}

.ticker-timeframes {
  display: flex;
  gap: 8px;
  margin-left: auto;
  white-space: nowrap;
}

.ticker-timeframes span:not(:last-child)::after {
  content: " •";
  margin-left: 8px;
  color: #4a5568;
}
```

2. CHART WRAPPER:
```css
.chart-wrapper {
  padding: 0 16px; /* Match ticker padding */
  width: calc(100% - 32px);
  margin: 0 auto;
}
```

3. PREVENT TEXT OVERFLOW:
For 30d text in Bitcoin Feed: reduce font-size or abbreviate long percentages
```css
.ticker-30d {
  font-size: 0.9em; /* Slightly smaller */
}
```

4. ALIGN BITCOIN TEXT WITH CHART:
Remove any margin/padding before "Bitcoin (BTC)" so it starts exactly at x=16px matching chart's left edge.
TEST: Bitcoin text left edge should align perfectly with chart's left edge at all screen sizes.
```


Tech stack: FastAPI, React, Docker, Redis
```

**Export key info**:
- Copy recent error messages
- Note completed features
- Current file being worked on
