import { WebSocketService } from './api';
import { Subject, filter, map, shareReplay } from 'rxjs';

// Create WebSocket instance with production-ready configuration
const ws = new WebSocketService();
const inbound$ = new Subject();

// Enhanced message handling with connection state tracking
ws.on('message', (data) => {
  try {
    console.log('[WS message]', data);
  } catch {}
  inbound$.next(data)
});

// Connection state events
ws.on('connected', () => {
  console.log('[Realtime] WebSocket connected');
  inbound$.next({ type: 'status', status: 'connected' });
});

ws.on('disconnected', (data) => {
  console.log('[Realtime] WebSocket disconnected', data);
  inbound$.next({ type: 'status', status: 'disconnected', data });
});

ws.on('error', (err) => {
  console.error('[Realtime] WebSocket error', err);
  inbound$.next({ type: 'status', status: 'error', error: err });
});

ws.on('reconnecting', () => {
  console.log('[Realtime] WebSocket reconnecting...');
  inbound$.next({ type: 'status', status: 'reconnecting' });
});

ws.on('connection_state_changed', (data) => {
  console.log('[Realtime] Connection state changed:', data.state);
  inbound$.next({ type: 'connection_state', state: data.state });
});

// Export connect function with retry logic
export const connectRealtime = () => {
  return ws.connect().catch((err) => {
    console.error('[Realtime] Connection failed:', err);
    // Will auto-retry based on WebSocketService configuration
  });
};

// Export disconnect function
export const disconnectRealtime = () => {
  ws.disconnect();
};

// Export reconnect function for manual reconnection
export const reconnectRealtime = () => {
  return ws.reconnect();
};

// Export WebSocket instance for direct access if needed
export const getWebSocketInstance = () => ws;

export const connection$ = inbound$.pipe(
  filter((m) => m && m.type === 'status'),
  shareReplay(1)
);

export const priceUpdates$ = inbound$.pipe(
  filter((m) => m && m.type === 'price_update'),
  map((m) => m.data),
  shareReplay(1)
);

export const alerts$ = inbound$.pipe(
  filter((m) => m && (m.type === 'chat_agent_message' || m.type === 'alert')),
  map((m) => {
    // Prefer single-source agent chat to avoid duplicates
    if (m.type === 'chat_agent_message') {
      const payload = { title: 'Agent', text: m.content };
      try { console.log('[Alerts$] agent message', payload); } catch {}
      return payload;
    }
    // If 'alert' still comes through, ignore to prevent duplication
    try { console.log('[Alerts$] dropped raw alert to avoid duplicates'); } catch {}
    return null;
  }),
  filter((x) => !!x),
  shareReplay(1)
);

// Intelligent prompt feed: stream of preloaded prompts pushed from backend
export const promptFeed$ = inbound$.pipe(
  filter((m) => m && m.type === 'prompt_feed'),
  map((m) => m.data || []),
  shareReplay(1)
);

export const sentimentShift$ = inbound$.pipe(
  filter((m) => m && m.type === 'sentiment_shift'),
  map((m) => m.data),
  shareReplay(1)
);


