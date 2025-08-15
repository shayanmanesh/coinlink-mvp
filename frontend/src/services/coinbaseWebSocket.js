// Deprecated: Client-side Coinbase WS removed; backend now provides ticker via WS
export class CoinbaseWebSocket {
  constructor() {
    this.ws = null;
    this.subscribers = new Set();
    this.reconnectTimeout = null;
    this.prices = new Map();
    this.priceHistory = new Map();
    this.isConnecting = false;
    this.isConnected = false;
    
    // Top 50 cryptocurrencies by market cap (excluding stablecoins)
    // Format: [symbol, product_id]
    this.topCryptos = [
      ['BTC', 'BTC-USD'],
      ['ETH', 'ETH-USD'],
      ['SOL', 'SOL-USD'],
      ['BNB', 'BNB-USD'],
      ['XRP', 'XRP-USD'],
      ['DOGE', 'DOGE-USD'],
      ['ADA', 'ADA-USD'],
      ['AVAX', 'AVAX-USD'],
      ['TRX', 'TRX-USD'],
      ['LINK', 'LINK-USD'],
      ['DOT', 'DOT-USD'],
      ['MATIC', 'MATIC-USD'],
      ['TON', 'TON-USD'],
      ['SHIB', 'SHIB-USD'],
      ['LTC', 'LTC-USD'],
      ['UNI', 'UNI-USD'],
      ['BCH', 'BCH-USD'],
      ['XLM', 'XLM-USD'],
      ['ATOM', 'ATOM-USD'],
      ['NEAR', 'NEAR-USD'],
      ['XMR', 'XMR-USD'],
      ['OP', 'OP-USD'],
      ['ARB', 'ARB-USD'],
      ['FIL', 'FIL-USD'],
      ['APT', 'APT-USD'],
      ['HBAR', 'HBAR-USD'],
      ['CRO', 'CRO-USD'],
      ['VET', 'VET-USD'],
      ['MKR', 'MKR-USD'],
      ['KAS', 'KAS-USD'],
      ['INJ', 'INJ-USD'],
      ['RUNE', 'RUNE-USD'],
      ['GRT', 'GRT-USD'],
      ['THETA', 'THETA-USD'],
      ['FTM', 'FTM-USD'],
      ['ALGO', 'ALGO-USD'],
      ['LDO', 'LDO-USD'],
      ['IMX', 'IMX-USD'],
      ['SUI', 'SUI-USD'],
      ['SEI', 'SEI-USD'],
      ['MANA', 'MANA-USD'],
      ['SAND', 'SAND-USD'],
      ['AXS', 'AXS-USD'],
      ['AAVE', 'AAVE-USD'],
      ['EOS', 'EOS-USD'],
      ['QNT', 'QNT-USD'],
      ['FLOW', 'FLOW-USD'],
      ['CHZ', 'CHZ-USD'],
      ['RNDR', 'RNDR-USD'],
      ['SNX', 'SNX-USD']
    ];
    
    // Map symbol to product_id
    this.symbolToProduct = new Map(this.topCryptos);
    
    // Store initial timestamps for percentage calculations
    this.timestamps = {
      start: Date.now(),
      oneHour: Date.now() - 3600000,
      twentyFourHours: Date.now() - 86400000,
      sevenDays: Date.now() - 604800000
    };
  }

  connect() {
    if (this.isConnecting || this.isConnected) {
      return;
    }

    this.isConnecting = true;
    
    try {
      // Connect to Coinbase WebSocket public feed
      this.ws = new WebSocket('wss://ws-feed.exchange.coinbase.com');
      
      this.ws.onopen = () => {
        console.log('WEBSOCKET CONNECTED to Coinbase');
        this.isConnecting = false;
        this.isConnected = true;
        
        // Subscribe to ticker channel for all products
        const subscribeMessage = {
          type: 'subscribe',
          product_ids: this.topCryptos.map(([_, productId]) => productId),
          channels: ['ticker']
        };
        
        this.ws.send(JSON.stringify(subscribeMessage));
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'ticker') {
            this.handleTickerUpdate(data);
          } else if (data.type === 'subscriptions') {
            console.log('Subscribed to channels:', data.channels);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.isConnected = false;
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnecting = false;
        this.isConnected = false;
        this.handleReconnect();
      };
      
    } catch (error) {
      console.error('Failed to connect to Coinbase WebSocket:', error);
      this.isConnecting = false;
      this.isConnected = false;
      this.handleReconnect();
    }
  }
  
  handleTickerUpdate(data) {
    const productId = data.product_id;
    const symbol = this.getSymbolFromProductId(productId);
    
    if (!symbol) return;
    
    const price = parseFloat(data.price);
    const time = new Date(data.time).getTime();
    
    // Store price history for percentage calculations
    if (!this.priceHistory.has(symbol)) {
      this.priceHistory.set(symbol, []);
    }
    
    const history = this.priceHistory.get(symbol);
    history.push({ price, time });
    
    // Keep only last 7 days of history
    const sevenDaysAgo = Date.now() - 604800000;
    const filteredHistory = history.filter(h => h.time > sevenDaysAgo);
    this.priceHistory.set(symbol, filteredHistory);
    
    // Calculate percentage changes
    const changes = this.calculatePercentageChanges(symbol, price, filteredHistory);
    
    // Update current price
    const prevPrice = this.prices.get(symbol);
    this.prices.set(symbol, {
      symbol,
      price,
      change_1h: changes.oneHour,
      change_24h: changes.twentyFourHours,
      change_7d: changes.sevenDays,
      volume_24h: parseFloat(data.volume_24h || 0),
      time: data.time,
      flash: prevPrice ? (price > prevPrice.price ? 'green' : price < prevPrice.price ? 'red' : null) : null
    });
    
    // Log first real price
    if (!prevPrice && symbol === 'BTC') {
      console.log(`WEBSOCKET CONNECTED - First REAL BTC price: $${price.toFixed(2)}`);
    }
    
    // Notify subscribers
    this.notifySubscribers();
  }
  
  calculatePercentageChanges(symbol, currentPrice, history) {
    if (history.length === 0) {
      return { oneHour: 0, twentyFourHours: 0, sevenDays: 0 };
    }
    
    const now = Date.now();
    const oneHourAgo = now - 3600000;
    const twentyFourHoursAgo = now - 86400000;
    const sevenDaysAgo = now - 604800000;
    
    // Find closest historical prices
    const oneHourPrice = this.findClosestPrice(history, oneHourAgo);
    const twentyFourHourPrice = this.findClosestPrice(history, twentyFourHoursAgo);
    const sevenDayPrice = this.findClosestPrice(history, sevenDaysAgo);
    
    return {
      oneHour: oneHourPrice ? ((currentPrice - oneHourPrice) / oneHourPrice * 100) : 0,
      twentyFourHours: twentyFourHourPrice ? ((currentPrice - twentyFourHourPrice) / twentyFourHourPrice * 100) : 0,
      sevenDays: sevenDayPrice ? ((currentPrice - sevenDayPrice) / sevenDayPrice * 100) : 0
    };
  }
  
  findClosestPrice(history, targetTime) {
    if (history.length === 0) return null;
    
    let closest = history[0];
    let minDiff = Math.abs(history[0].time - targetTime);
    
    for (const item of history) {
      const diff = Math.abs(item.time - targetTime);
      if (diff < minDiff) {
        minDiff = diff;
        closest = item;
      }
    }
    
    return closest.price;
  }
  
  getSymbolFromProductId(productId) {
    for (const [symbol, id] of this.symbolToProduct) {
      if (id === productId) {
        return symbol;
      }
    }
    return null;
  }
  
  handleReconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    this.reconnectTimeout = setTimeout(() => {
      console.log('Attempting to reconnect to Coinbase WebSocket...');
      this.connect();
    }, 3000);
  }
  
  subscribe(callback) {
    this.subscribers.add(callback);
    
    // Send current data immediately
    if (this.prices.size > 0) {
      callback(this.getCurrentData());
    }
  }
  
  unsubscribe(callback) {
    this.subscribers.delete(callback);
  }
  
  notifySubscribers() {
    const data = this.getCurrentData();
    this.subscribers.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error in subscriber callback:', error);
      }
    });
  }
  
  getCurrentData() {
    const cryptoData = [];
    const btcData = this.prices.get('BTC');
    
    // Prepare ticker data
    for (const [symbol, data] of this.prices) {
      cryptoData.push({
        symbol,
        price: data.price,
        change_24h: data.change_24h,
        flash: data.flash
      });
    }
    
    // Sort by market cap rank (approximate order)
    const symbolOrder = this.topCryptos.map(([symbol]) => symbol);
    cryptoData.sort((a, b) => {
      const aIndex = symbolOrder.indexOf(a.symbol);
      const bIndex = symbolOrder.indexOf(b.symbol);
      return aIndex - bIndex;
    });
    
    return {
      cryptoData,
      bitcoinData: btcData ? {
        price: btcData.price,
        change1h: btcData.change_1h,
        change24h: btcData.change_24h,
        change7d: btcData.change_7d,
        volume24h: btcData.volume_24h,
        flash: btcData.flash
      } : null
    };
  }
  
  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.subscribers.clear();
  }
}

// No-op singleton to avoid import errors in any older code paths
export const coinbaseWS = new CoinbaseWebSocket();