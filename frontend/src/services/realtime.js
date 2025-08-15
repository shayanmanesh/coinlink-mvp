import { WebSocketService } from './api';
import { Subject, filter, map, shareReplay } from 'rxjs';

const ws = new WebSocketService();
const inbound$ = new Subject();

ws.on('message', (data) => {
  try {
    console.log('[WS message]', data);
  } catch {}
  inbound$.next(data)
});
ws.on('connected', () => inbound$.next({ type: 'status', status: 'connected' }));
ws.on('disconnected', (data) => inbound$.next({ type: 'status', status: 'disconnected', data }));
ws.on('error', (err) => inbound$.next({ type: 'status', status: 'error', error: err }));

export const connectRealtime = () => ws.connect().catch(() => {});

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


