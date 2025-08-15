import axios from 'axios';

// API base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Global rate-limit friendly handling and auto-retry (single retry)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    try {
      const status = error?.response?.status;
      const config = error?.config || {};
      if (status === 429 && !config._retry) {
        console.warn('Too many requests. Retrying in 5s...');
        config._retry = true;
        await new Promise((r) => setTimeout(r, 5000));
        return api.request(config);
      }
    } catch {}
    return Promise.reject(error);
  }
);

// Bitcoin Analysis API
export const bitcoinAPI = {
  // Chat with Bitcoin analyst (with optional auth token)
  async chat(message, sessionId = 'default', authToken = null) {
    try {
      const headers = {};
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }
      const response = await api.post('/api/chat', 
        { message, session_id: sessionId, token: authToken },
        { headers }
      );
      return response.data;
    } catch (error) {
      console.error('Chat API error:', error);
      throw error;
    }
  },

  // Get current Bitcoin price
  async getPrice() {
    try {
      const response = await api.get('/api/bitcoin/price');
      return response.data;
    } catch (error) {
      console.error('Price API error:', error);
      throw error;
    }
  },

  // Get Bitcoin sentiment
  async getSentiment() {
    try {
      const response = await api.get('/api/bitcoin/sentiment');
      return response.data;
    } catch (error) {
      console.error('Sentiment API error:', error);
      throw error;
    }
  },

  // Get market summary
  async getMarketSummary() {
    try {
      const response = await api.get('/api/bitcoin/market-summary');
      return response.data;
    } catch ( error) {
      console.error('Market summary API error:', error);
      throw error;
    }
  },

  // Get Bitcoin news
  async getNews(limit = 10) {
    try {
      const response = await api.get(`/api/bitcoin/news?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('News API error:', error);
      throw error;
    }
  },

  // Analyze text sentiment
  async analyzeText(text) {
    try {
      const response = await api.post('/api/bitcoin/analyze', { text });
      return response.data;
    } catch (error) {
      console.error('Text analysis API error:', error);
      throw error;
    }
  },
};

// Alerts API
export const alertsAPI = {
  // Get active alerts
  async getActiveAlerts() {
    try {
      const response = await api.get('/api/alerts');
      return response.data;
    } catch (error) {
      console.error('Alerts API error:', error);
      throw error;
    }
  },

  // Get alert history
  async getAlertHistory(limit = 20) {
    try {
      const response = await api.get(`/api/alerts/history?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Alert history API error:', error);
      throw error;
    }
  },
};

// Chat API
export const chatAPI = {
  // Get chat history
  async getChatHistory() {
    try {
      const response = await api.get('/api/chat/history');
      return response.data;
    } catch (error) {
      console.error('Chat history API error:', error);
      throw error;
    }
  },
};

// Authentication API
export const authAPI = {
  // Sign up
  async signup(email, password) {
    try {
      const response = await api.post('/api/v2/auth/signup', { email, password });
      return response.data;
    } catch (error) {
      console.error('Signup API error:', error);
      throw error;
    }
  },
  
  // Login
  async login(email, password) {
    try {
      const response = await api.post('/api/v2/auth/login', { email, password });
      return response.data;
    } catch (error) {
      console.error('Login API error:', error);
      throw error;
    }
  },
  
  // Verify authentication
  async verify(token) {
    try {
      const response = await api.get('/api/v2/auth/verify', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      console.error('Verify API error:', error);
      throw error;
    }
  },
  
  // Check rate limit
  async checkRateLimit(token = null) {
    try {
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await api.get('/api/v2/auth/rate-limit', { headers });
      return response.data;
    } catch (error) {
      console.error('Rate limit API error:', error);
      throw error;
    }
  }
};

// System API
export const systemAPI = {
  // Health check
  async healthCheck() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check API error:', error);
      throw error;
    }
  },

  // Get connection count
  async getConnectionCount() {
    try {
      const response = await api.get('/api/connections');
      return response.data;
    } catch (error) {
      console.error('Connection count API error:', error);
      throw error;
    }
  },

  // Get contextual prompts
  async getContextualPrompts() {
    try {
      const response = await api.get('/api/prompts');
      return response.data?.prompts || [];
    } catch (error) {
      console.error('Prompts API error:', error);
      return [];
    }
  },
};

// WebSocket connection helper
export class WebSocketService {
  constructor(url = WS_BASE_URL) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.listeners = new Map();
  }

  connect() {
    return new Promise((resolve, reject) => {
      try {
        try { console.log('[WS] connecting to', this.url); } catch {}
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            // Handle ping messages by responding with pong
            if (data.type === 'ping') {
              this.send({ type: 'pong', timestamp: new Date().toISOString() });
              return;
            }
            
            // Ensure we're not passing the event object itself
            if (data && typeof data === 'object' && !data.type) {
              // Add a timestamp if not present
              if (!data.timestamp) {
                data.timestamp = new Date().toISOString();
              }
            }
            // Guard against Event-like payloads
            const isEventLike = data && (data.type === 'Event' || data.target !== undefined || data.currentTarget !== undefined);
            if (!isEventLike) {
              this.emit('message', data);
            }
          } catch (error) {
            console.error('WebSocket message parse error:', error);
            // Send a safe error message
            this.emit('error', { 
              message: 'Failed to parse message', 
              timestamp: new Date().toISOString() 
            });
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          // Only pass safe, serializable data
          const safeData = {
            code: event.code || 0,
            reason: event.reason || 'Unknown reason',
            timestamp: new Date().toISOString()
          };
          this.emit('disconnected', safeData);
          
          // Don't reconnect if it was a manual close or server shutdown
          if (event.code === 1000 || event.code === 1001) {
            console.log('WebSocket closed normally, not reconnecting');
            return;
          }
          
          // Attempt to reconnect with exponential backoff
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 10000);
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
            setTimeout(() => {
              this.reconnectAttempts++;
              this.connect().catch(err => {
                console.error('Reconnection failed:', err);
              });
            }, delay);
          } else {
            console.log('Max reconnection attempts reached');
            this.emit('reconnection_failed', { 
              message: 'Failed to reconnect after maximum attempts',
              timestamp: new Date().toISOString()
            });
          }
        };

        this.ws.onerror = (error) => {
          try {
            console.error('WebSocket error occurred');
          } catch {}
          // Only pass safe, serializable data - never pass the error object directly
          const safeData = {
            message: 'WebSocket connection error occurred',
            timestamp: new Date().toISOString()
          };
          this.emit('error', safeData);
          // Don't reject with the raw error object
          reject(new Error('WebSocket connection failed'));
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected');
    }
  }

  // Event listener system
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          // Ensure we're not passing event objects to React components
          if (data && typeof data === 'object') {
            // Check if it's a DOM Event object
            if (data.type === 'Event' || data.target !== undefined || data.currentTarget !== undefined) {
              console.warn('Preventing event object from being passed to component');
              return;
            }
            
            // Check if it's a WebSocket Event object
            if (data.type === 'error' && data.error !== undefined) {
              console.warn('Preventing WebSocket error event from being passed to component');
              return;
            }
          }
          
          callback(data);
        } catch (error) {
          console.error('Event listener error:', error);
        }
      });
    }
  }
}

// Create named API instance
const apiInstance = {
  bitcoin: bitcoinAPI,
  alerts: alertsAPI,
  chat: chatAPI,
  system: systemAPI,
  WebSocketService,
};

// Export default API instance
export default apiInstance;
